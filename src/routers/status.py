from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}

@router.get("/version")
async def version():
    """Return API version information."""
    return {
        "version": "0.1.0",
        "api_version": "v1"
    }