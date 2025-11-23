"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1 import containers, missions

router = APIRouter()

router.include_router(containers.router, prefix="/containers", tags=["containers"])
router.include_router(missions.router, prefix="/missions", tags=["missions"])

