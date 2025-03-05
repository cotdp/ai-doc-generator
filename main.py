from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
import os
import uvicorn
from dotenv import load_dotenv
from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.report import ReportRequest, ReportStatus

# Load environment variables
load_dotenv('.env.local')

# Initialize FastAPI app
app = FastAPI(
    title="AI Document Generator",
    description="An AI-powered system for generating research reports",
    version="0.1.0"
)

# Initialize orchestrator
orchestrator = OrchestratorAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}

@app.post("/generate-report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate a report based on the provided topic.
    
    Args:
        request (ReportRequest): The report generation request
        background_tasks (BackgroundTasks): FastAPI background tasks
        
    Returns:
        Dict: The task ID and initial status
    """
    try:
        # Start report generation in background
        task = {
            "topic": request.topic,
            "template_type": request.template_type,
            "max_pages": request.max_pages,
            "include_images": request.include_images
        }
        
        background_tasks.add_task(orchestrator.execute, task)
        
        return {
            "task_id": orchestrator.active_tasks[-1].id if orchestrator.active_tasks else None,
            "status": "accepted",
            "message": f"Report generation started for topic: {request.topic}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report-status/{task_id}")
async def get_report_status(task_id: str):
    """
    Get the status of a report generation task.
    
    Args:
        task_id (str): The task ID
        
    Returns:
        ReportStatus: The task status
    """
    status = orchestrator.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@app.get("/download-report/{task_id}")
async def download_report(task_id: str):
    """
    Download a generated report.
    
    Args:
        task_id (str): The task ID
        
    Returns:
        FileResponse: The generated report file
    """
    status = orchestrator.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Report not ready yet")
    
    from fastapi.responses import FileResponse
    
    # Get the report file path from the task status
    file_path = f"output/{status.topic.replace(' ', '_')}.docx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(file_path)
    )

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    ) 