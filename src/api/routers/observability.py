"""LLM Observability and Token/Cost Tracking Router."""

from typing import Any

from fastapi import APIRouter, Depends

from src.api.auth import verify_auth
from src.config import load_config
from src.storage.repository import StorageRepository

router = APIRouter(prefix="/observability", tags=["Observability"], dependencies=[Depends(verify_auth)])


@router.get("/stats")
async def get_observability_metrics() -> dict[str, Any]:
    """Retrieve cumulative LLM token consumption, latency, and estimated cost."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    return repo.get_observability_stats()
