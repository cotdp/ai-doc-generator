import json
import uuid
from typing import Any, Dict, List

from ..models.report import ReportRequest, ReportStatus
from .base_agent import BaseAgent
from .content_writer_agent import ContentWriterAgent
from .document_structure_agent import DocumentStructureAgent
from .web_research_agent import WebResearchAgent

PLAN_SYSTEM_PROMPT = """You are an expert research planner. Your task is to break down a research topic 
into a clear execution plan with specific research questions and sections to investigate. Focus on creating a comprehensive plan that will 
result in detailed, substantive content about the specific topic requested by the user."""


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
            id=task_id, status="in_progress", topic=request.topic
        )

        try:
            # Log the primary topic being researched
            self.logger.info(f"Starting report generation on topic: {request.topic}")

            # 1. Generate execution plan
            plan = await self._generate_plan(request.topic)

            # 2. Conduct research for each section
            research_results = await self._conduct_research(plan, request.topic)

            # 3. Generate document structure
            structure = await self.structure_agent.execute(
                {
                    "topic": request.topic,
                    "research": research_results,
                    "template_type": request.template_type,
                    "max_pages": request.max_pages,
                }
            )

            # 4. Generate content
            content = await self.writer_agent.execute(
                {
                    "structure": structure,
                    "research": research_results,
                    "max_pages": request.max_pages,
                    "topic": request.topic,  # Explicitly pass the topic
                }
            )

            self.active_tasks[task_id].status = "completed"
            return {"task_id": task_id, "status": "completed", "content": content}

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
        prompt = f"""Create a detailed research plan for the topic: '{topic}'. 

IMPORTANT INSTRUCTIONS:
1. Include key areas to investigate and specific questions to answer about '{topic}'
2. Ensure that all questions directly relate to '{topic}' without drifting to general methodology
3. Create questions that will yield substantive content about '{topic}', not explanations of what different document sections are
4. Focus on research questions that will provide real insights, statistics, examples, and analysis of '{topic}'
5. DO NOT include any timelines, dates, or scheduling information - this research will be executed immediately
6. Structure questions by conceptual areas rather than by time periods or phases

Format your response as a structured JSON with sections and questions."""

        response = await self._call_llm(PLAN_SYSTEM_PROMPT, prompt)

        try:
            # Assume response is in a structured format
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple section-based plan
            self.logger.warning(
                "Failed to parse JSON response from plan generation. Using fallback plan."
            )
            return [{"section": "Overview", "questions": [topic]}]

    async def _conduct_research(
        self, plan: List[Dict[str, Any]], main_topic: str
    ) -> List[Dict[str, Any]]:
        """Conduct research based on the execution plan.

        Args:
            plan (List[Dict[str, Any]]): The research plan
            main_topic (str): The main research topic

        Returns:
            List[Dict[str, Any]]: The research results
        """
        research_results = []

        for section in plan:
            # Ensure each question includes the main topic for context
            section_questions = section.get("questions", [])
            contextualized_questions = []

            for question in section_questions:
                # Only add main_topic if it's not already in the question
                if main_topic.lower() not in question.lower():
                    contextualized_question = f"{question} (regarding {main_topic})"
                else:
                    contextualized_question = question
                contextualized_questions.append(contextualized_question)

            section_research = await self.web_research_agent.execute(
                {
                    "questions": contextualized_questions,
                    "context": f"Researching for a report on: {main_topic}. Section: {section['section']}",
                    "main_topic": main_topic,
                }
            )

            research_results.append(
                {
                    "section": section["section"],
                    "research": section_research,
                    "topic": main_topic,
                }
            )

        return research_results

    def get_task_status(self, task_id: str) -> ReportStatus:
        """Get the status of a report generation task.

        Args:
            task_id (str): The task ID

        Returns:
            ReportStatus: The task status
        """
        return self.active_tasks.get(task_id)
