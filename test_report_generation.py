import asyncio
import os
import time
import logging
import sys
from dotenv import load_dotenv
from src.agents.orchestrator_agent import OrchestratorAgent

async def generate_test_report(topic: str = None):
    """Generate a test report on an interesting topic."""
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Create test request
    task = {
        "topic": topic or "The Future of Quantum Computing: Current Progress and Applications",
        "template_type": "business",
        "max_pages": 12,
        "include_images": True
    }
    
    print(f"Starting report generation for topic: {task['topic']}")
    
    try:
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
        else:
            print("\nError: Report file not found!")
            if not content_path:
                print("No content path was returned in the result")
            print(f"Full result: {result}")
            
    except Exception as e:
        print(f"\nError generating report: {str(e)}")
        logging.exception("Detailed error information:")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable debug logging for specific modules
    logging.getLogger('langchain_community.utilities.dalle_image_generator').setLevel(logging.DEBUG)
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
    print("Starting end-to-end test...")
    start_time = time.time()
    
    try:
        # Get topic from command line argument if provided
        topic = sys.argv[1] if len(sys.argv) > 1 else None
        asyncio.run(generate_test_report(topic))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logging.exception("Detailed error information:")
    finally:
        end_time = time.time()
        print(f"\nTotal execution time: {end_time - start_time:.2f} seconds") 