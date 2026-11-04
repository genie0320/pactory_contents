"""Configuration loader for the pipeline."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import yaml
from pydantic import BaseModel, Field


class PathSettings(BaseModel):
    data_dir: Path = Path("./data")
    inbox_dir: Path = Path("./data/inbox")
    archive_dir: Path = Path("./data/archive")
    processed_dir: Path = Path("./data/processed")
    texts_dir: Path = Path("./data/processed/texts")
    metadata_dir: Path = Path("./data/processed/metadata")
    assets_dir: Path = Path("./data/processed/assets")
    index_dir: Path = Path("./data/index")
    db_path: Path = Path("./data/index/catalog.db")
    outputs_dir: Path = Path("./data/outputs")


class ImageFilterSettings(BaseModel):
    min_width: int = 250
    min_height: int = 150
    min_aspect_ratio: float = 0.2
    max_aspect_ratio: float = 5.0


class ExtractionSettings(BaseModel):
    concurrency: int = 5
    max_retries: int = 4
    retry_backoff_factor: float = 2.0
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"


class RetrievalSettings(BaseModel):
    top_k_candidates: int = 15
    bm25_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "title": 2.0,
            "core_problem": 2.5,
            "reframing_logic": 3.0,
            "solution_framework": 2.0,
            "topic_tags": 2.5,
            "notable_episodes": 1.5,
        }
    )
    jaccard_threshold: float = 0.5


class TaxonomySettings(BaseModel):
    categories: List[str] = Field(
        default_factory=lambda: [
            "업무스킬",
            "서비스기획/AI",
            "마케팅/브랜딩",
            "커리어/이직",
            "부업/수익화",
            "자기관리",
        ]
    )


class AppConfig(BaseModel):
    paths: PathSettings = Field(default_factory=PathSettings)
    image_filter: ImageFilterSettings = Field(default_factory=ImageFilterSettings)
    extraction: ExtractionSettings = Field(default_factory=ExtractionSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    taxonomy: TaxonomySettings = Field(default_factory=TaxonomySettings)

    def ensure_directories(self) -> None:
        """Create runtime data directories if they do not exist."""
        for path_field in [
            self.paths.data_dir,
            self.paths.inbox_dir,
            self.paths.archive_dir,
            self.paths.processed_dir,
            self.paths.texts_dir,
            self.paths.metadata_dir,
            self.paths.assets_dir,
            self.paths.index_dir,
            self.paths.outputs_dir,
        ]:
            path_field.mkdir(parents=True, exist_ok=True)


def load_config(config_file: Optional[str | Path] = None) -> AppConfig:
    """Load configuration from YAML file and environment variables."""
    cfg_path = Path(config_file) if config_file else Path("config.yaml")
    data: Dict[str, Any] = {}
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    # Override with env vars if present
    if "CATALOG_DB_PATH" in os.environ:
        if "paths" not in data:
            data["paths"] = {}
        data["paths"]["db_path"] = os.environ["CATALOG_DB_PATH"]

    config = AppConfig(**data)
    return config
