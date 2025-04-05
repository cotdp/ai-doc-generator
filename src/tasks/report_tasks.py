import logging
import os
from typing import Dict, Any, List, Optional

from celery import Task, group, chain
from sqlalchemy.orm import Session

from .worker import app
from src.database import SessionLocal
from src.database.models import Report, TaskStatus, Task, TaskType
from src.agents.web_research_agent import WebResearchAgent
from src.agents.document_structure_agent import DocumentStructureAgent
from src.agents.content_writer_agent import ContentWriterAgent
from src.agents.image_generation_agent import ImageGenerationAgent
from src.models.report import ReportRequest, ReportSection, ReportStructure

# Setup logger
logger = logging.getLogger(__name__)


class SqlAlchemyTask(Task):
    """Base class for Celery tasks that need database access."""
    
    _session = None
    
    @property
    def session(self) -> Session:
        """Get a database session."""
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def after_return(self, *args, **kwargs):
        """Close the database session after the task returns."""
        if self._session is not None:
            self._session.close()
            self._session = None


@app.task(bind=True, base=SqlAlchemyTask)
def generate_report(self, report_id: int, task_id: str) -> Dict[str, Any]:
    """Main task to orchestrate the report generation process.

    Args:
        report_id: The ID of the report in the database
        task_id: The UUID of the report generation task

    Returns:
        Dict[str, Any]: The task result
    """
    logger.info(f"Starting report generation task {task_id} for report {report_id}")
    
    try:
        # Get the report from the database
        db = self.session
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            logger.error(f"Report {report_id} not found")
            return {"success": False, "error": "Report not found"}
            
        # Update the report status
        report.status = TaskStatus.IN_PROGRESS
        report.progress = 0.05
        db.commit()
        
        # Create subtasks in the database
        research_task = Task(
            report_id=report.id,
            task_type=TaskType.RESEARCH,
            status=TaskStatus.PENDING
        )
        structure_task = Task(
            report_id=report.id,
            task_type=TaskType.STRUCTURE,
            status=TaskStatus.PENDING
        )
        content_task = Task(
            report_id=report.id,
            task_type=TaskType.CONTENT,
            status=TaskStatus.PENDING
        )
        image_task = Task(
            report_id=report.id,
            task_type=TaskType.IMAGE,
            status=TaskStatus.PENDING
        )
        
        db.add_all([research_task, structure_task, content_task, image_task])
        db.commit()
        
        # Create the task chain
        result = chain(
            research_topic.s(report.id, research_task.id),
            generate_structure.s(report.id, structure_task.id),
            generate_content.s(report.id, content_task.id),
            generate_images.s(report.id, image_task.id)
        ).apply_async()
        
        return {
            "success": True,
            "task_id": task_id,
            "report_id": report_id,
            "celery_task_id": result.id
        }
        
    except Exception as e:
        logger.error(f"Error starting report generation: {str(e)}")
        # Update the report status to failed
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = TaskStatus.FAILED
                report.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating report status: {str(db_error)}")
            
        return {"success": False, "error": str(e)}


@app.task(bind=True, base=SqlAlchemyTask)
def research_topic(self, report_id: int, task_id: int) -> Dict[str, Any]:
    """Research a topic using the WebResearchAgent.

    Args:
        report_id: The ID of the report in the database
        task_id: The ID of the task in the database

    Returns:
        Dict[str, Any]: The research results
    """
    logger.info(f"Starting research task for report {report_id}")
    
    try:
        # Get the report and task from the database
        db = self.session
        report = db.query(Report).filter(Report.id == report_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not report or not task:
            logger.error(f"Report {report_id} or task {task_id} not found")
            return {"success": False, "error": "Report or task not found"}
            
        # Update the task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = db.func.now()
        db.commit()
        
        # Update report progress
        report.progress = 0.1
        db.commit()
        
        # Initialize the WebResearchAgent
        agent = WebResearchAgent()
        
        # Generate research plan
        # Simple example queries - in production this would be more complex
        queries = [
            f"What is {report.topic}?",
            f"Latest developments in {report.topic}",
            f"Key statistics about {report.topic}",
            f"Future trends for {report.topic}"
        ]
        
        # Execute the research
        context = f"Researching for a report on: {report.topic}"
        research_results = agent.execute_sync({
            "questions": queries,
            "context": context,
            "main_topic": report.topic
        })
        
        # Update the task status
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.result_data = {"research": [r.dict() for r in research_results]}
        task.completed_at = db.func.now()
        
        # Update report progress
        report.progress = 0.25
        
        db.commit()
        
        return {"success": True, "research": [r.dict() for r in research_results]}
        
    except Exception as e:
        logger.error(f"Error in research task: {str(e)}")
        # Update the task status to failed
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating task status: {str(db_error)}")
            
        return {"success": False, "error": str(e)}


@app.task(bind=True, base=SqlAlchemyTask)
def generate_structure(self, research_result: Dict[str, Any], report_id: int, task_id: int) -> Dict[str, Any]:
    """Generate a document structure using the DocumentStructureAgent.

    Args:
        research_result: The research results from the previous task
        report_id: The ID of the report in the database
        task_id: The ID of the task in the database

    Returns:
        Dict[str, Any]: The structure generation results
    """
    logger.info(f"Starting structure generation task for report {report_id}")
    
    try:
        # Check if research was successful
        if not research_result.get("success", False):
            return {"success": False, "error": "Research task failed"}
            
        # Get the report and task from the database
        db = self.session
        report = db.query(Report).filter(Report.id == report_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not report or not task:
            logger.error(f"Report {report_id} or task {task_id} not found")
            return {"success": False, "error": "Report or task not found"}
            
        # Update the task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = db.func.now()
        db.commit()
        
        # Update report progress
        report.progress = 0.35
        db.commit()
        
        # Get the template from the database
        template = report.template if report.template_id else None
        template_type = template.template_type.value if template else "standard"
        
        # Initialize the DocumentStructureAgent
        agent = DocumentStructureAgent()
        
        # Execute the structure generation
        structure = agent.execute_sync({
            "topic": report.topic,
            "research": research_result.get("research", []),
            "template_type": template_type,
            "max_pages": report.max_pages
        })
        
        # Update the task status
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.result_data = {"structure": structure.dict()}
        task.completed_at = db.func.now()
        
        # Update report progress
        report.progress = 0.5
        
        db.commit()
        
        return {
            "success": True,
            "structure": structure.dict(),
            "research": research_result.get("research", [])
        }
        
    except Exception as e:
        logger.error(f"Error in structure generation task: {str(e)}")
        # Update the task status to failed
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating task status: {str(db_error)}")
            
        return {"success": False, "error": str(e)}


@app.task(bind=True, base=SqlAlchemyTask)
def generate_content(self, structure_result: Dict[str, Any], report_id: int, task_id: int) -> Dict[str, Any]:
    """Generate content for a document using the ContentWriterAgent.

    Args:
        structure_result: The structure generation results from the previous task
        report_id: The ID of the report in the database
        task_id: The ID of the task in the database

    Returns:
        Dict[str, Any]: The content generation results
    """
    logger.info(f"Starting content generation task for report {report_id}")
    
    try:
        # Check if structure generation was successful
        if not structure_result.get("success", False):
            return {"success": False, "error": "Structure generation task failed"}
            
        # Get the report and task from the database
        db = self.session
        report = db.query(Report).filter(Report.id == report_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not report or not task:
            logger.error(f"Report {report_id} or task {task_id} not found")
            return {"success": False, "error": "Report or task not found"}
            
        # Update the task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = db.func.now()
        db.commit()
        
        # Update report progress
        report.progress = 0.6
        db.commit()
        
        # Initialize the ContentWriterAgent
        agent = ContentWriterAgent()
        
        # Convert structure dict back to a ReportStructure object
        structure_dict = structure_result.get("structure", {})
        structure = ReportStructure(**structure_dict)
        
        # Execute the content generation
        output_path = agent.execute_sync({
            "structure": structure,
            "research": structure_result.get("research", []),
            "include_images": report.include_images,
            "max_concurrent_tasks": 2  # Limit concurrency in task
        })
        
        # Update the task status
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.result_data = {"output_path": output_path}
        task.completed_at = db.func.now()
        
        # Update report progress and file path
        report.file_path = output_path
        report.progress = 0.8 if report.include_images else 1.0
        report.status = TaskStatus.COMPLETED if not report.include_images else TaskStatus.IN_PROGRESS
        
        db.commit()
        
        return {
            "success": True,
            "output_path": output_path,
            "include_images": report.include_images,
            "structure": structure_dict
        }
        
    except Exception as e:
        logger.error(f"Error in content generation task: {str(e)}")
        # Update the task status to failed
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating task status: {str(db_error)}")
            
        return {"success": False, "error": str(e)}


@app.task(bind=True, base=SqlAlchemyTask)
def generate_images(self, content_result: Dict[str, Any], report_id: int, task_id: int) -> Dict[str, Any]:
    """Generate images for a document using the ImageGenerationAgent.

    Args:
        content_result: The content generation results from the previous task
        report_id: The ID of the report in the database
        task_id: The ID of the task in the database

    Returns:
        Dict[str, Any]: The image generation results
    """
    logger.info(f"Starting image generation task for report {report_id}")
    
    try:
        # Check if content generation was successful
        if not content_result.get("success", False):
            return {"success": False, "error": "Content generation task failed"}
            
        # Get the report and task from the database
        db = self.session
        report = db.query(Report).filter(Report.id == report_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not report or not task:
            logger.error(f"Report {report_id} or task {task_id} not found")
            return {"success": False, "error": "Report or task not found"}
            
        # If images are not included, skip this task
        if not report.include_images:
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.result_data = {"skipped": True}
            task.completed_at = db.func.now()
            db.commit()
            return {"success": True, "skipped": True}
            
        # Update the task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = db.func.now()
        db.commit()
        
        # Update report progress
        report.progress = 0.9
        db.commit()
        
        # Initialize the ImageGenerationAgent
        agent = ImageGenerationAgent()
        
        # Extract image descriptions from the structure
        structure_dict = content_result.get("structure", {})
        descriptions = []
        
        # Helper function to extract image descriptions from sections
        def extract_image_descriptions(sections):
            for section in sections:
                if "content" in section and "![" in section["content"]:
                    # Extract image descriptions using simple parsing
                    content = section["content"]
                    start_idx = content.find("![")
                    while start_idx != -1:
                        end_idx = content.find(")", start_idx)
                        if end_idx != -1:
                            img_text = content[start_idx:end_idx+1]
                            alt_start = img_text.find("[")+1
                            alt_end = img_text.find("]", alt_start)
                            desc_start = img_text.find("(")+1
                            desc_end = img_text.find(")", desc_start)
                            
                            if alt_start > 0 and alt_end > alt_start and desc_start > 0 and desc_end > desc_start:
                                alt_text = img_text[alt_start:alt_end]
                                description = img_text[desc_start:desc_end]
                                descriptions.append((description, alt_text))
                                
                        start_idx = content.find("![" ,end_idx)
                
                # Check subsections recursively
                if "subsections" in section and section["subsections"]:
                    extract_image_descriptions(section["subsections"])
        
        # Extract image descriptions
        if "sections" in structure_dict:
            extract_image_descriptions(structure_dict["sections"])
        
        # Generate the images
        if descriptions:
            result = agent.execute_sync({
                "batch": True,
                "descriptions": descriptions,
                "size": "1792x1024",
                "quality": "standard",
                "style": "abstract"
            })
        else:
            result = {"success": True, "image_paths": [], "message": "No image descriptions found"}
        
        # Update the task status
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.result_data = {"images": result}
        task.completed_at = db.func.now()
        
        # Update report progress and status
        report.progress = 1.0
        report.status = TaskStatus.COMPLETED
        
        db.commit()
        
        return {
            "success": True,
            "images": result,
            "output_path": content_result.get("output_path")
        }
        
    except Exception as e:
        logger.error(f"Error in image generation task: {str(e)}")
        # Update the task status to failed
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                db.commit()
                
            # Even if image generation fails, the report can still be considered complete
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = TaskStatus.COMPLETED
                report.progress = 1.0
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating task status: {str(db_error)}")
            
        return {"success": False, "error": str(e)}