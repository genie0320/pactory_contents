"""LLM Observability and Token/Cost Tracking Router."""

from typing import Any

from fastapi import APIRouter, Depends

from src.api.auth import verify_auth
from src.api.dependencies import RepoDep

router = APIRouter(prefix="/observability", tags=["Observability"], dependencies=[Depends(verify_auth)])


@router.get("/stats")
async def get_observability_metrics(repo: RepoDep) -> dict[str, Any]:
    """Retrieve cumulative LLM token consumption, latency, and estimated cost."""
    return repo.get_observability_stats()
