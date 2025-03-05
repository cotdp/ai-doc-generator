import os
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from ..models.report import ReportSection, ReportStructure
from .base_agent import BaseAgent

STRUCTURE_SYSTEM_PROMPT = """You are an expert document architect. Your task is to:
1. Organize research into a comprehensive, detailed structure
2. Create clear section hierarchies with multiple subsections
3. Plan extensive content flow with detailed sections
4. Ensure complete, in-depth coverage of all aspects of the topic
5. Design a structure that allows for maximum depth in each section
6. Create a framework that supports 1000-1500 words per major section"""


class DocumentStructureAgent(BaseAgent):
    """Agent responsible for creating document structure from research."""

    def __init__(self, temperature: float = 0.3):
        """Initialize the document structure agent with the o3-mini model.

        Args:
            temperature (float): The temperature for model responses (note: o3-mini only supports temperature=1)
        """
        # o3-mini model doesn't support temperature parameter except temperature=1
        # Initialize with no temperature parameter
        super().__init__(model="o3-mini")

        # Override the LLM with max_tokens parameter
        self.llm = ChatOpenAI(
            model="o3-mini", api_key=os.getenv("OPENAI_API_KEY"), max_tokens=10000
        )

    async def execute(self, task: Dict[str, Any]) -> ReportStructure:
        """Create document structure from research results.

        Args:
            task (Dict[str, Any]): Task containing research results and parameters

        Returns:
            ReportStructure: The organized document structure
        """
        topic = task["topic"]
        research = task["research"]
        template_type = task.get("template_type", "standard")
        max_pages = task.get("max_pages", 10)  # Default to 10 pages if not specified

        # Get base template
        template = self._get_template(template_type)

        # Generate structure from research
        structure_prompt = self._create_structure_prompt(
            topic, research, template, max_pages
        )
        structure_response = await self._call_llm(
            STRUCTURE_SYSTEM_PROMPT, structure_prompt, response_format="json"
        )

        # Parse and validate structure
        if isinstance(structure_response, dict):
            sections = self._convert_to_sections(structure_response)
        else:
            # Fallback to simple section parsing
            sections = self._parse_structure(str(structure_response))

        # Create the final structure
        structure = ReportStructure(
            title=topic,
            sections=sections,
            metadata={
                "template_type": template_type,
                "research_sections": len(research),
                "total_sections": len(sections),
                "target_pages": max_pages,
            },
        )

        # Save structure to temporary file for progressive saving and recovery
        import json
        import os

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Format filename for structure JSON
        filename = topic.replace(" ", "_").replace(":", "_").replace("/", "_")
        structure_path = f"output/{filename}_structure.json"

        # Save structure as JSON
        with open(structure_path, "w") as f:
            f.write(structure.model_dump_json(indent=2))

        self.logger.info(f"Document structure saved to {structure_path}")

        return structure

    def _get_template(self, template_type: str) -> Dict[str, Any]:
        """Get the base template for the document structure.

        Args:
            template_type (str): The type of template to use

        Returns:
            Dict[str, Any]: The template structure
        """
        templates = {
            "standard": {
                "sections": [
                    "Executive Summary",
                    "Introduction",
                    "Background",
                    "Methodology",
                    "Findings",
                    "Analysis",
                    "Conclusions",
                    "Recommendations",
                    "References",
                ]
            },
            "academic": {
                "sections": [
                    "Abstract",
                    "Introduction",
                    "Literature Review",
                    "Methodology",
                    "Results",
                    "Discussion",
                    "Conclusion",
                    "References",
                ]
            },
            "business": {
                "sections": [
                    "Executive Summary",
                    "Market Analysis",
                    "Industry Trends",
                    "Competitive Analysis",
                    "Recommendations",
                    "Implementation Plan",
                    "References",
                ]
            },
        }

        return templates.get(template_type, templates["standard"])

    def _create_structure_prompt(
        self,
        topic: str,
        research: List[Dict[str, Any]],
        template: Dict[str, Any],
        max_pages: int,
    ) -> str:
        """Create a prompt for generating document structure.

        Args:
            topic (str): The document topic
            research (List[Dict[str, Any]]): The research results
            template (Dict[str, Any]): The template to use
            max_pages (int): The target number of pages for the document

        Returns:
            str: The prompt for generating document structure
        """
        # Prepare research summaries
        research_summaries = []
        for i, result in enumerate(research):
            # Use get with a default value to handle missing keys
            title = result.get("title", f"Research Item {i+1}")
            # If there's a 'section' key, use that as a fallback
            if "section" in result and not title.startswith("Research Item"):
                title = result["section"]

            # If there's content, include a snippet
            content_snippet = ""
            if "content" in result and result["content"]:
                content = result["content"]
                content_snippet = (
                    f" - {content[:100]}..." if len(content) > 100 else f" - {content}"
                )

            summary = f"Research {i+1}: {title}{content_snippet}"
            research_summaries.append(summary)

        research_text = "\n".join(research_summaries)

        # Get template sections
        template_sections = template.get("sections", [])
        template_text = "\n".join([f"- {section}" for section in template_sections])

        # Determine structure density based on page count
        if max_pages <= 5:
            detail_level = "Create a concise structure with focused sections and minimal subsections"
            subsection_guidance = (
                "For each major section, include 1-2 key subsections to maintain focus"
            )
        elif max_pages <= 10:
            detail_level = "Create a balanced structure with major sections and appropriate subsections"
            subsection_guidance = "For each major section, include 2-3 subsections to provide adequate detail"
        else:
            detail_level = "Create a highly detailed structure with major sections and multiple subsections"
            subsection_guidance = "For each major section, include 3-5 subsections to allow for detailed content"

        return f"""Create a clear, structured outline for a professional report on: {topic}

RESEARCH AVAILABLE:
{research_text}

TEMPLATE STRUCTURE:
{template_text}

TARGET LENGTH: {max_pages} pages (Approximately 500 words per page)

REQUIREMENTS:
1. {detail_level}
2. Each major section should support {500 * max_pages // len(template_sections)}-{750 * max_pages // len(template_sections)} words of content
3. Include sufficient subsections to meet the target page count of {max_pages} pages
4. Ensure the structure allows exploration of all critical aspects of the topic
5. Add any missing sections needed for complete coverage
6. Ensure a logical flow between sections
7. Use clear, descriptive titles for all sections
8. Organize the structure to meet the target page count while maintaining quality

INSTRUCTIONS:
- {subsection_guidance}
- Ensure sections are organized logically with a clear narrative flow
- Maintain academic/professional tone in section titles
- Adapt the template as needed to fit the topic, adding or removing sections to match the target length
- Design the structure to be comprehensive while meeting the {max_pages}-page target

Your response should have this JSON structure:
{{
  "title": "Report title",
  "sections": [
    {{
      "title": "Major Section 1",
      "content": "",
      "subsections": [
        {{ "title": "Subsection 1.1", "content": "" }},
        {{ "title": "Subsection 1.2", "content": "" }}
      ]
    }},
    {{
      "title": "Major Section 2",
      "content": "",
      "subsections": [
        {{ "title": "Subsection 2.1", "content": "" }},
        {{ "title": "Subsection 2.2", "content": "" }}
      ]
    }}
  ]
}}

Create the report structure now, focusing on delivering a structure that fits within {max_pages} pages while providing comprehensive coverage of {topic}."""

    def _parse_structure(self, structure_response: str) -> List[ReportSection]:
        """Parse the LLM response into a list of sections.

        Args:
            structure_response (str): The LLM's structure response

        Returns:
            List[ReportSection]: The parsed sections
        """
        try:
            # Try to parse as JSON first
            import json

            structure_data = json.loads(structure_response)
            return self._convert_to_sections(structure_data)
        except json.JSONDecodeError:
            # Fallback to simple section parsing
            sections = []
            current_section = None

            for line in structure_response.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if not line.startswith("  "):  # Main section
                    if current_section:
                        sections.append(current_section)
                    current_section = ReportSection(
                        title=line, content="", subsections=[]
                    )
                elif current_section:  # Subsection
                    current_section.subsections.append(
                        ReportSection(title=line.strip(), content="")
                    )

            if current_section:
                sections.append(current_section)

            return sections

    def _convert_to_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Convert parsed JSON data to ReportSection objects.

        Args:
            data (Dict[str, Any]): The parsed structure data

        Returns:
            List[ReportSection]: The converted sections
        """
        sections = []

        for section_data in data.get("sections", []):
            section = ReportSection(
                title=section_data["title"],
                content=section_data.get("content", ""),
                subsections=[
                    ReportSection(**subsection)
                    for subsection in section_data.get("subsections", [])
                ],
            )
            sections.append(section)

        return sections
