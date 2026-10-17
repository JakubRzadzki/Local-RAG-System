"""``/api/health`` endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/health", tags=["health"])


class HealthOut(BaseModel):
    status: str


@router.get("", response_model=HealthOut)
async def health() -> HealthOut:
    """Liveness probe."""
    return HealthOut(status="ok")
