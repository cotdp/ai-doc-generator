import asyncio
import os
import time
import logging
import sys
from dotenv import load_dotenv
import unittest
from unittest.mock import patch, MagicMock
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.content_writer_agent import ContentWriterAgent
from src.agents.document_structure_agent import DocumentStructureAgent
from src.models.report import ReportSection, ReportStructure

class TestMarkdownConversion(unittest.TestCase):
    """Test the markdown conversion functionality in the content writer agent."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Load environment variables
        load_dotenv('.env.local')
        
        # Check for required API keys
        if not os.getenv('OPENAI_API_KEY'):
            raise Exception("Error: OPENAI_API_KEY not found in .env.local")
        
        # Create output directory
        os.makedirs('output', exist_ok=True)
        os.makedirs('output/images', exist_ok=True)
        os.makedirs('output/test', exist_ok=True)
    
    async def test_markdown_conversion(self):
        """Test the conversion of all markdown elements to DOCX."""
        
        # Initialize content writer agent
        writer_agent = ContentWriterAgent()
        
        # Create a predefined section with all markdown elements
        section = ReportSection(
            title="Markdown Conversion Test",
            content=self._generate_test_markdown()
        )
        
        # Create a simple structure with one section
        structure = ReportStructure(
            title="Markdown Conversion Test",
            sections=[
                section
            ],
            metadata={"template_type": "standard", "max_pages": 5, "test_mode": True}
        )
        
        # Sample research data
        research = [
            {
                "title": "Markdown Test",
                "content": "This is sample research content for testing markdown conversion.",
                "source": "Test Source",
                "credibility_score": 0.9
            }
        ]
        
        # Execute content writer
        output_path = await writer_agent.execute({
            "structure": structure,
            "research": research,
            "include_images": True
        })
        
        # Verify results
        self.assertTrue(os.path.exists(output_path), f"Output file not found: {output_path}")
        file_size = os.path.getsize(output_path) / 1024  # Convert to KB
        print(f"Success! Test document generated at: {output_path}")
        print(f"File size: {file_size:.2f} KB")
        
        return output_path
    
    def _generate_test_markdown(self):
        """Generate test markdown content with all supported elements."""
        return """
# Main Heading

This is a paragraph with **bold text**, *italic text*, and `code`. This tests the basic formatting.

This paragraph has **bold text with *nested italic* inside it** and also *italic text with **nested bold** inside it*.

## Subheading Level 2

### Subheading Level 3

Here's a link to [OpenAI](https://openai.com) for testing link formatting. This sentence has **bold** and a [link](https://example.com) in the same paragraph.

#### Lists

Unordered list:
- Item 1 with **bold text**
- Item 2 with *italic text*
- Item 3 with `code` and [a link](https://example.com)

Numbered list with formatting:
1. First item with **bold**
2. Second item with *italic*
3. Third item with `code`

List with custom numbering (should be normalized):
41. This should be properly numbered as 1
42. This should be properly numbered as 2
43. This should be properly numbered as 3

#### Table

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| **Bold** | *Italic* | `Code`   |
| [Link](https://example.com) | Mixed **bold** and *italic* | Data 3 |
| Data 4   | Data 5   | Data 6   |

#### Blockquote

> This is a blockquote to test how blockquotes are formatted in the document.
> It includes **bold text** and *italic text* to test inline formatting.

#### Code Block

```python
def hello_world():
    print("Hello, World!")
    return True
```

#### Image

![Test Diagram](A detailed technical diagram showing a system architecture with multiple components, connections, and data flows, using a clean modern design style with blue and gray colors)

#### Combined Elements

1. **Bold item** with a [link](https://example.com)
2. *Italic item* with `code snippet`
3. Mixed **bold** and *italic* formatting in the same line

Final paragraph with combined **bold**, *italic*, and `code` elements to test inline formatting handling.
"""

async def run_test():
    """Run the markdown conversion test."""
    test = TestMarkdownConversion()
    TestMarkdownConversion.setUpClass()
    await test.test_markdown_conversion()

if __name__ == "__main__":
    print("Starting markdown conversion test...")
    start_time = time.time()
    
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logging.exception("Detailed error information:")
    finally:
        end_time = time.time()
        print(f"\nTotal execution time: {end_time - start_time:.2f} seconds") 