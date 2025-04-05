import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Get Redis URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
app = Celery("ai_doc_generator",
            broker=REDIS_URL,
            backend=REDIS_URL,
            include=["src.tasks.report_tasks"])

# Set timezone
app.conf.timezone = "UTC"

# Set task serialization format
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

# Configure task queues
app.conf.task_routes = {
    "src.tasks.report_tasks.generate_report": {"queue": "reports"},
    "src.tasks.report_tasks.research_topic": {"queue": "research"},
    "src.tasks.report_tasks.generate_structure": {"queue": "structure"},
    "src.tasks.report_tasks.generate_content": {"queue": "content"},
    "src.tasks.report_tasks.generate_images": {"queue": "images"},
}

# Configure task default rate limits
app.conf.task_default_rate_limit = "10/m"

# Configure task time limits
app.conf.task_time_limit = 1800  # 30 minutes
app.conf.task_soft_time_limit = 1500  # 25 minutes

if __name__ == "__main__":
    app.start()