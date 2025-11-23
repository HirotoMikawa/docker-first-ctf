"""
Container management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional

from app.core.rate_limiter import limiter
from app.core.config import settings

router = APIRouter()


class ContainerStartRequest(BaseModel):
    """Request model for starting a container"""
    user_id: str
    image: str = "python:3.11-slim"
    flag: str


class ContainerStartResponse(BaseModel):
    """Response model for container start"""
    status: str
    container_id: Optional[str] = None
    port: Optional[int] = None
    message: Optional[str] = None


@router.post("/start", response_model=ContainerStartResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def start_container(
    request: Request,
    data: ContainerStartRequest
):
    """
    Start a new container for a mission (Rate Limited: 5 req/min)
    """
    docker_manager = request.app.state.docker_manager
    
    try:
        result = await docker_manager.start_container(
            user_id=data.user_id,
            image=data.image,
            flag=data.flag
        )
        return ContainerStartResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{container_id}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def stop_container(
    request: Request,
    container_id: str
):
    """
    Stop and remove a container (Rate Limited: 5 req/min)
    """
    docker_manager = request.app.state.docker_manager
    
    success = await docker_manager.stop_container(container_id)
    if not success:
        raise HTTPException(status_code=404, detail="Container not found")
    
    return {"status": "success", "message": "Container stopped"}

