"""Health check endpoints for TMS API."""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Health check endpoint to verify API availability."""
    return {
        "status": "healthy",
        "service": "TMS Event-Driven API",
        "version": "1.0.0"
    }
