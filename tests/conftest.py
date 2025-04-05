import sys
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add the project root directory to Python's module search path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Load test environment variables
load_dotenv(root_dir / ".env.test")

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Create output directories
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Make sure environment variables are set
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test_openai_api_key"
    if not os.environ.get("PERPLEXITY_API_KEY"):
        os.environ["PERPLEXITY_API_KEY"] = "test_perplexity_api_key"