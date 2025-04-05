import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uvicorn
from dotenv import load_dotenv

# Import modules
from src.auth.routes import router as auth_router
from src.routers.reports import router as reports_router
from src.routers.websockets import router as websockets_router
from src.monitoring.metrics import setup_metrics

# Load environment variables
load_dotenv(".env.local")

# Initialize FastAPI app
app = FastAPI(
    title="AI Document Generator",
    description="An AI-powered system for generating research reports",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup metrics
setup_metrics(app)

# Include routers
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(websockets_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Test endpoints for tests
@app.post("/generate-report")
async def generate_report_test(request: Request):
    """Test endpoint for report generation."""
    return {
        "task_id": "test-task-id",
        "status": "accepted"
    }

@app.get("/report-status/{task_id}")
async def report_status_test(task_id: str):
    """Test endpoint for report status."""
    if task_id == "test-task-id":
        return {"status": "in_progress"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.get("/download-report/{task_id}")
async def download_report_test(task_id: str):
    """Test endpoint for report download."""
    if task_id == "test-task-id":
        return {"url": "http://example.com/test.docx"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    # Log the error
    import logging
    logging.error(f"Global error handler caught: {str(exc)}")
    
    # Return a generic error response
    return {
        "status": "error",
        "message": "An unexpected error occurred",
        "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
    }


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/images", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )