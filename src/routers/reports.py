import os
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.database.models import Report, User, ReportTemplate, TaskStatus
from src.models.report import ReportRequest
from src.auth.dependencies import get_current_active_user
from src.tasks.report_tasks import generate_report
from src.monitoring.metrics import report_generation_duration, active_reports_gauge
from src.websockets import get_connection_manager

# Create router
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new report generation task.
    
    Args:
        request: Report request
        background_tasks: FastAPI background tasks
        current_user: Current user
        db: Database session
        
    Returns:
        dict: Report creation information
    """
    # Start metrics timer
    start_time = time.time()
    
    # Get template if specified
    template = None
    if request.template_type != "standard":
        template = db.query(ReportTemplate).filter(
            ReportTemplate.template_type == request.template_type
        ).first()
    
    # Create report in database
    task_id = str(uuid.uuid4())
    report = Report(
        task_id=task_id,
        user_id=current_user.id,
        template_id=template.id if template else None,
        topic=request.topic,
        max_pages=request.max_pages,
        include_images=request.include_images,
        status=TaskStatus.PENDING,
        progress=0.0
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Increment active reports gauge
    active_reports_gauge.inc()
    
    try:
        # Generate report in Celery task
        generate_report.delay(report.id, task_id)
        
        # Update metrics when completed
        report_generation_duration.labels(
            template_type=request.template_type,
            success="true"
        ).observe(time.time() - start_time)
        
        # Return report information
        return {
            "task_id": task_id,
            "report_id": report.id,
            "status": "accepted",
            "message": f"Report generation started for topic: {request.topic}"
        }
    except Exception as e:
        # Update metrics on failure
        report_generation_duration.labels(
            template_type=request.template_type,
            success="false"
        ).observe(time.time() - start_time)
        active_reports_gauge.dec()
        
        # Update report status
        report.status = TaskStatus.FAILED
        report.error = str(e)
        db.commit()
        
        # Raise exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting report generation: {str(e)}"
        )


@router.get("/{task_id}")
async def get_report_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the status of a report generation task.
    
    Args:
        task_id: Report task ID
        current_user: Current user
        db: Database session
        
    Returns:
        dict: Report status
        
    Raises:
        HTTPException: If the report is not found or belongs to another user
    """
    # Get report from database
    report = db.query(Report).filter(Report.task_id == task_id).first()
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check if report belongs to current user
    if report.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    # Return report status
    return {
        "id": report.task_id,
        "status": report.status.value,
        "topic": report.topic,
        "progress": report.progress,
        "error": report.error
    }


@router.get("/{task_id}/download")
async def download_report(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download a generated report.
    
    Args:
        task_id: Report task ID
        current_user: Current user
        db: Database session
        
    Returns:
        FileResponse: The generated report file
        
    Raises:
        HTTPException: If the report is not found, belongs to another user, is not complete, or the file doesn't exist
    """
    # Get report from database
    report = db.query(Report).filter(Report.task_id == task_id).first()
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check if report belongs to current user
    if report.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    # Check if report is complete
    if report.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report not ready yet"
        )
    
    # Check if file exists
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Return file
    return FileResponse(
        report.file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(report.file_path)
    )


@router.get("/")
async def list_reports(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """List reports for current user.
    
    Args:
        current_user: Current user
        db: Database session
        limit: Maximum number of reports to return
        offset: Offset for pagination
        
    Returns:
        dict: List of reports and total count
    """
    # Get reports from database
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Get total count
    total = db.query(Report).filter(Report.user_id == current_user.id).count()
    
    # Return reports
    return {
        "reports": [
            {
                "id": report.task_id,
                "topic": report.topic,
                "status": report.status.value,
                "progress": report.progress,
                "created_at": report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
            }
            for report in reports
        ],
        "total": total
    }