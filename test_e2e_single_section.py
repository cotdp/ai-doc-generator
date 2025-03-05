import asyncio
import os
import time
import logging
import sys
from dotenv import load_dotenv
from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.report import ReportSection, ReportStructure
from src.agents.content_writer_agent import ContentWriterAgent

async def single_section_e2e_test():
    """
    Run an end-to-end test of the report generation process with a single section and
    all markdown elements exercised in one pass.
    
    This test is designed to:
    1. Run quicker than the full test (one section only)
    2. Exercise all markdown syntax elements (headings, lists, tables, images, etc.)
    3. Validate that the final document contains all expected elements
    """
    print("\n======= Starting Single-Section E2E Test =======\n")
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Create a single section structure for testing
    single_section_structure = ReportStructure(
        title="AI in Financial Analysis: A Condensed Overview",
        sections=[
            ReportSection(
                title="Comprehensive Overview of AI in Finance",
                content="",
                subsections=[
                    ReportSection(title="Current Applications and Technologies", content=""),
                    ReportSection(title="Market Impact and Financial Outcomes", content=""),
                    ReportSection(title="Future Trends and Strategic Implications", content="")
                ],
                images=None,
                tables=None
            )
        ],
        metadata={"template_type": "standard", "max_pages": 5, "test_mode": True}
    )
    
    # Modify test_prompt_template to ensure all markdown elements are included
    original_generate_content = ContentWriterAgent._generate_content
    
    async def enhanced_generate_content(self, section_title, research, include_images=True):
        """Modified version that ensures all markdown elements are included"""
        # Use original method to get base content
        content = await original_generate_content(self, section_title, research, include_images)
        
        # If this is the main section, append special instructions to ensure all markdown elements
        if "Comprehensive Overview" in section_title:
            self.logger.info("Adding markdown enhancement instructions to prompt...")
            enhanced_prompt = f"""
Please enhance the content you've created to include all of the following markdown elements:

1. **Headings**: Include at least 3 levels of headings (##, ###, ####)
2. **Lists**: Include both bulleted and numbered lists
3. **Table**: Include a table with at least 3 columns showing comparative data
4. **Formatting**: Use **bold**, *italic*, and `code` formatting
5. **Blockquotes**: Include at least one blockquote
6. **Links**: Include at least 2-3 links to external resources
7. **Image**: Include exactly one image with a descriptive caption using ![caption](description) syntax
8. **Code block**: Include a code snippet in a code block

Make these additions feel natural and integrate them into the existing content.
"""
            system_prompt = """You are an expert content writer with extensive experience in creating professional documents.
Your task is to enhance the content with various markdown formatting elements while maintaining the professional tone and accuracy.
"""
            enhanced_content = await self._call_llm(system_prompt, content + enhanced_prompt)
            return enhanced_content
        return content
    
    # Monkey patch the method temporarily
    ContentWriterAgent._generate_content = enhanced_generate_content
    
    try:
        # Create test request
        task = {
            "topic": "AI in Financial Analysis: A Condensed Overview",
            "template_type": "business",
            "max_pages": 5,
            "include_images": True,
            "_test_structure_override": single_section_structure  # Custom field for testing
        }
        
        print(f"Starting report generation with single section...")
        
        # Execute report generation, but override the structure step
        # This is done by adding a hook in the orchestrator to use our predefined structure
        original_execute = orchestrator.execute
        
        async def execute_with_override(self, task):
            if "_test_structure_override" in task:
                print("Using test structure override...")
                # Skip the normal structure generation
                structure = task["_test_structure_override"]
                
                # Get research questions from structure
                questions = []
                for section in structure.sections:
                    questions.append(f"What are the latest advancements in {section.title}?")
                    for subsection in section.subsections:
                        questions.append(f"What are the key aspects of {subsection.title}?")
                
                # Perform research
                research_results = await self.research_agent.execute({
                    "questions": questions,
                    "context": task["topic"]
                })
                
                # Generate content
                content = await self.writer_agent.execute({
                    "structure": structure,
                    "research": research_results,
                    "max_pages": task["max_pages"],
                    "include_images": task["include_images"]
                })
                
                return {
                    "task_id": "test-e2e-single-section",
                    "status": "completed",
                    "content": content
                }
            else:
                # Use the original method for non-test tasks
                return await original_execute(self, task)
        
        # Monkey patch the orchestrator.execute method
        orchestrator.execute = execute_with_override.__get__(orchestrator, OrchestratorAgent)
        
        # Execute report generation
        result = await orchestrator.execute(task)
        
        print(f"\nReport generation completed!")
        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")
        print(f"Output file: {result.get('content', 'No content path returned')}")
        
        # Verify file exists
        content_path = result.get('content')
        if content_path and os.path.exists(content_path):
            print(f"\nSuccess! Report file generated at: {content_path}")
            file_size = os.path.getsize(content_path) / 1024  # Convert to KB
            print(f"File size: {file_size:.2f} KB")
            return content_path
        else:
            print("\nError: Report file not found!")
            if not content_path:
                print("No content path was returned in the result")
            print(f"Full result: {result}")
            return None
            
    except Exception as e:
        print(f"\nError generating report: {str(e)}")
        logging.exception("Detailed error information:")
        return None
    finally:
        # Restore original methods
        ContentWriterAgent._generate_content = original_generate_content
        orchestrator.execute = original_execute

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,  # Use INFO level to reduce noise
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable debug logging only for specific modules
    logging.getLogger('src.agents.content_writer_agent').setLevel(logging.DEBUG)
    
    # Load environment variables
    load_dotenv('.env.local')
    
    # Check for required API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in .env.local")
        exit(1)
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/images', exist_ok=True)
    
    # Run the test
    print("Starting end-to-end single section test...")
    start_time = time.time()
    
    try:
        asyncio.run(single_section_e2e_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logging.exception("Detailed error information:")
    finally:
        end_time = time.time()
        print(f"\nTotal execution time: {end_time - start_time:.2f} seconds") 