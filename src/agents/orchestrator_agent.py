from typing import Any, Dict, List
from .base_agent import BaseAgent
from .web_research_agent import WebResearchAgent
from .document_structure_agent import DocumentStructureAgent
from .content_writer_agent import ContentWriterAgent
from ..models.report import ReportRequest, ReportStatus
import uuid
import json

PLAN_SYSTEM_PROMPT = """You are an expert research planner. Your task is to break down a research topic 
into a clear execution plan with specific research questions and sections to investigate."""

class OrchestratorAgent(BaseAgent):
    """Main agent that orchestrates the report generation process."""
    
    def __init__(self):
        """Initialize the orchestrator agent with its sub-agents."""
        super().__init__()
        self.web_research_agent = WebResearchAgent()
        self.structure_agent = DocumentStructureAgent()
        self.writer_agent = ContentWriterAgent()
        self.active_tasks: Dict[str, ReportStatus] = {}
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the report generation process.
        
        Args:
            task (Dict[str, Any]): The report generation task
            
        Returns:
            Dict[str, Any]: The generation results
        """
        request = ReportRequest(**task)
        task_id = str(uuid.uuid4())
        self.active_tasks[task_id] = ReportStatus(
            id=task_id,
            status="in_progress",
            topic=request.topic
        )
        
        try:
            # 1. Generate execution plan
            plan = await self._generate_plan(request.topic)
            
            # 2. Conduct research for each section
            research_results = await self._conduct_research(plan)
            
            # 3. Generate document structure
            structure = await self.structure_agent.execute({
                "topic": request.topic,
                "research": research_results,
                "template_type": request.template_type
            })
            
            # 4. Generate content
            content = await self.writer_agent.execute({
                "structure": structure,
                "research": research_results,
                "max_pages": request.max_pages
            })
            
            self.active_tasks[task_id].status = "completed"
            return {
                "task_id": task_id,
                "status": "completed",
                "content": content
            }
            
        except Exception as e:
            self.logger.error(f"Error in report generation: {str(e)}")
            self.active_tasks[task_id].status = "failed"
            self.active_tasks[task_id].error = str(e)
            raise
    
    async def _generate_plan(self, topic: str) -> List[Dict[str, Any]]:
        """Generate an execution plan for the research topic.
        
        Args:
            topic (str): The research topic
            
        Returns:
            List[Dict[str, Any]]: The execution plan
        """
        prompt = f"Create a detailed research plan for the topic: {topic}. Include key areas to investigate and specific questions to answer."
        response = await self._call_llm(PLAN_SYSTEM_PROMPT, prompt)
        
        try:
            # Assume response is in a structured format
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple section-based plan
            return [{"section": "Overview", "questions": [topic]}]
    
    async def _conduct_research(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Conduct research based on the execution plan.
        
        Args:
            plan (List[Dict[str, Any]]): The research plan
            
        Returns:
            List[Dict[str, Any]]: The research results
        """
        research_results = []
        
        for section in plan:
            section_research = await self.web_research_agent.execute({
                "questions": section["questions"],
                "context": section.get("context", "")
            })
            research_results.append({
                "section": section["section"],
                "research": section_research
            })
        
        return research_results
    
    def get_task_status(self, task_id: str) -> ReportStatus:
        """Get the status of a report generation task.
        
        Args:
            task_id (str): The task ID
            
        Returns:
            ReportStatus: The task status
        """
        return self.active_tasks.get(task_id) 