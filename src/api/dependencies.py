"""FastAPI dependencies for shared config, repository access, and response builders."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, HTTPException

from src.api.schemas.generator import SeedAssetsResponse, VisualAssetResponseItem
from src.api.schemas.inbox import ArticleSummaryItem
from src.config import AppConfig, load_config
from src.storage.repository import StorageRepository


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache the application configuration."""
    return load_config()


def get_repo(
    config: Annotated[AppConfig, Depends(get_config)],
) -> StorageRepository:
    """Provide a StorageRepository instance initialized with the current config."""
    return StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)


RepoDep = Annotated[StorageRepository, Depends(get_repo)]
ConfigDep = Annotated[AppConfig, Depends(get_config)]


def build_seed_assets_response(repo: StorageRepository, doc_ids: list[str]) -> SeedAssetsResponse:
    """Build unified visual assets response across multiple seed doc IDs."""
    items: list[VisualAssetResponseItem] = []
    for did in doc_ids:
        art = repo.get_article(did)
        title = art.title if art else did
        for a in repo.get_visual_assets(did):
            items.append(
                VisualAssetResponseItem(
                    doc_id=did,
                    doc_title=title,
                    asset_id=a.asset_id,
                    page_no=a.page_no,
                    file_path=a.file_path,
                    image_url=f"/api/media/assets/{a.file_path}",
                    caption=a.caption,
                    width=a.width,
                    height=a.height,
                )
            )
    return SeedAssetsResponse(total=len(items), assets=items)


def build_article_detail(repo: StorageRepository, doc_id: str) -> dict[str, Any]:
    """Retrieve complete metadata, visual assets, and text preview for a single article/seed."""
    article = repo.get_article(doc_id)
    if not article:
        raise HTTPException(status_code=404, detail="해당 문서를 찾을 수 없습니다.")

    meta = repo.get_article_metadata(doc_id)
    assets = repo.get_visual_assets(doc_id)
    text_content = repo.get_processed_text(doc_id)

    archetype_val = None
    reusable_assets = []
    if meta:
        archetype_val = (
            meta.article_archetype.value
            if hasattr(meta.article_archetype, "value")
            else str(meta.article_archetype)
        )
        reusable_assets = [
            (t.value if hasattr(t, "value") else str(t))
            for t in (meta.reusable_asset_types or [])
        ]

    return {
        "article": ArticleSummaryItem(
            doc_id=article.doc_id,
            title=article.title,
            author=article.author,
            published_date=article.published_date,
            source_format=article.source_format,
            char_count=article.char_count,
            image_count=article.image_count,
            status=article.status.value if hasattr(article.status, "value") else str(article.status),
            primary_category=meta.primary_category if meta else None,
            article_archetype=archetype_val,
            core_thesis=meta.core_thesis if meta else None,
            reusable_asset_types=reusable_assets,
            target_audience=meta.target_audience if meta else None,
            core_problem=meta.core_problem if meta else None,
            reframing_logic=meta.reframing_logic if meta else None,
            hook_strategy=meta.hook_strategy if meta else None,
            solution_framework=meta.solution_framework if meta else [],
            notable_episodes=meta.notable_episodes if meta else [],
            topic_tags=meta.topic_tags if meta else [],
            ingested_at=article.ingested_at.isoformat() if hasattr(article.ingested_at, "isoformat") else (str(article.ingested_at) if article.ingested_at else None),
            indexed_at=article.indexed_at.isoformat() if hasattr(article.indexed_at, "isoformat") else (str(article.indexed_at) if article.indexed_at else None),
        ),
        "visual_assets": [
            {
                "asset_id": ass.asset_id,
                "asset_type": "image",
                "page_no": ass.page_no,
                "file_path": str(ass.file_path),
                "image_url": f"/api/media/assets/{doc_id}/{Path(ass.file_path).name}" if ass.file_path else None,
                "width": ass.width,
                "height": ass.height,
                "caption": ass.caption,
            }
            for ass in assets
        ],
        "preview_text": (text_content[:2000] + "...") if text_content and len(text_content) > 2000 else (text_content or ""),
        "full_text": text_content or "",
    }
