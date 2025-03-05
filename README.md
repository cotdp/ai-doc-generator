# AI Document Generator

An AI-powered system for generating research reports using FastAPI, LangChain, and Perplexity AI.

## Features

- Automated research on any topic using Perplexity AI
- Multiple report templates (standard, academic, business)
- Rich text formatting with tables and images
- Citation tracking and credibility scoring
- Asynchronous report generation
- Progress tracking and status updates
- Microsoft Word (DOCX) output

## Prerequisites

- Python 3.10 or higher
- Docker (optional)
- API Keys:
  - Perplexity AI API key
  - OpenAI API key

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-doc-generator.git
   cd ai-doc-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env.local` file:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API keys
   ```

5. Run the application:
   ```bash
   python main.py
   ```

### Docker Development

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Usage

The API will be available at http://localhost:8000

### API Endpoints

- `POST /generate-report`
  ```json
  {
    "topic": "Your research topic",
    "template_type": "standard",
    "max_pages": 10,
    "include_images": true
  }
  ```

- `GET /report-status/{task_id}`
  - Check the status of a report generation task

- `GET /download-report/{task_id}`
  - Download the generated report (DOCX format)

- `GET /health`
  - Health check endpoint

### Example

```python
import requests

# Start report generation
response = requests.post(
    "http://localhost:8000/generate-report",
    json={
        "topic": "Sustainable Finance in Indonesia",
        "template_type": "business",
        "max_pages": 15,
        "include_images": True
    }
)

task_id = response.json()["task_id"]

# Check status
status = requests.get(f"http://localhost:8000/report-status/{task_id}")

# Download report when completed
if status.json()["status"] == "completed":
    report = requests.get(f"http://localhost:8000/download-report/{task_id}")
```

## Testing

Run tests with pytest:
```bash
pytest
```

## Deployment

The application includes GitHub Actions workflows for CI/CD:

1. Automated testing on pull requests
2. Docker image building and pushing to Docker Hub
3. Deployment to your chosen cloud platform

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 