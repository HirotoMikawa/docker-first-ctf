"""
Mission endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_missions():
    """List available missions"""
    return {
        "missions": [
            {
                "id": "sample01",
                "title": "Sample Mission 01",
                "description": "First challenge mission"
            }
        ]
    }

