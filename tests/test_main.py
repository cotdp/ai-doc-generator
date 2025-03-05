from fastapi.testclient import TestClient
import pytest
from main import app
import os

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_generate_report():
    """Test the report generation endpoint."""
    request_data = {
        "topic": "Test Topic",
        "template_type": "standard",
        "max_pages": 5,
        "include_images": True
    }
    
    response = client.post("/generate-report", json=request_data)
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["status"] == "accepted"

def test_report_status_not_found():
    """Test the report status endpoint with invalid task ID."""
    response = client.get("/report-status/invalid-id")
    assert response.status_code == 404

def test_download_report_not_found():
    """Test the download endpoint with invalid task ID."""
    response = client.get("/download-report/invalid-id")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_full_report_generation():
    """Test the complete report generation flow."""
    # 1. Start report generation
    request_data = {
        "topic": "Test Integration",
        "template_type": "standard",
        "max_pages": 3,
        "include_images": False
    }
    
    response = client.post("/generate-report", json=request_data)
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    
    # 2. Check status (it should be in progress or completed)
    response = client.get(f"/report-status/{task_id}")
    assert response.status_code == 200
    status = response.json()
    assert status["status"] in ["in_progress", "completed"]
    
    # Note: In a real test, we would wait for completion
    # For this test, we'll just verify the endpoint works 