"""Draft Generation and Synthesis API router."""

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from src.api.auth import verify_auth
from src.api.schemas.generator import (
    BlueprintGenerateRequest,
    BlueprintGenerateResponse,
    DraftSynthesizeRequest,
    DraftSynthesizeResponse,
    SeedCandidateItem,
    SeedSearchRequest,
    SeedSearchResponse,
)
from src.config import load_config
from src.exceptions import LLMServiceError
from src.extraction.llm_client import LLMClient
from src.models import ArticleArchetype, SeedRoleAssignment, SynthesisBlueprint
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.synthesis.planner import SynthesisPlanner
from src.synthesis.synthesizer import ArticleSynthesizer

router = APIRouter(prefix="/draft", tags=["Draft Generation"], dependencies=[Depends(verify_auth)])


def _build_seed_assignments(
    repo: StorageRepository,
    selected_ids: List[str],
    topic: str,
    direction: str,
) -> List[SeedRoleAssignment]:
    """Build SeedRoleAssignment objects from explicitly selected doc_ids."""
    role_order = ["domain_case", "perspective_framework", "synthesis_counterpoint"]
    assignments: List[SeedRoleAssignment] = []

    for idx, did in enumerate(selected_ids):
        art = repo.get_article(did)
        meta = repo.get_article_metadata(did)
        if not art or not meta:
            continue
        role = role_order[idx] if idx < len(role_order) else "supplementary_evidence"
        assignments.append(
            SeedRoleAssignment(
                seed_type=role,
                doc_id=art.doc_id,
                title=art.title,
                reason=f"사용자 선택 시드 ({role})",
                metadata=meta,
            )
        )
    return assignments


@router.post("/seeds", response_model=SeedSearchResponse)
async def search_seed_candidates(req: SeedSearchRequest):
    """Search and rank relevant Seed articles for the given topic and direction."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    retriever = SeedRetriever(config=config, repo=repo)

    # 1. Retrieve candidates
    candidates = retriever.search_candidates(topic=req.topic, direction=req.direction, top_k=req.limit)

    # 2. Get role recommendations
    try:
        recommended_seeds = retriever.retrieve_seeds(topic=req.topic, user_direction=req.direction, count=3)
        role_map = {s.doc_id: s.seed_type for s in recommended_seeds}
    except Exception:
        role_map = {}

    items: List[SeedCandidateItem] = []
    for art, meta, rank in candidates:
        items.append(
            SeedCandidateItem(
                doc_id=art.doc_id,
                title=art.title,
                archetype=meta.article_archetype.value if hasattr(meta.article_archetype, "value") else str(meta.article_archetype),
                target_audience=meta.target_audience,
                core_thesis=meta.core_thesis,
                solution_framework=meta.solution_framework,
                notable_episodes=meta.notable_episodes,
                topic_tags=meta.topic_tags,
                relevance_score=round(abs(rank), 2),
                assigned_role=role_map.get(art.doc_id),
            )
        )

    return SeedSearchResponse(
        topic=req.topic,
        direction=req.direction,
        total_found=len(items),
        candidates=items,
    )


@router.post("/blueprint", response_model=BlueprintGenerateResponse)
async def generate_blueprint(req: BlueprintGenerateRequest):
    """Generate structured synthesis blueprint outline."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    llm = LLMClient()
    if not llm.api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM API Key (GEMINI_API_KEY) is required to generate blueprints.",
        )

    retriever = SeedRetriever(config=config, repo=repo)
    if req.selected_seed_ids:
        seeds = _build_seed_assignments(repo, req.selected_seed_ids, req.topic, req.direction)
    else:
        seeds = retriever.retrieve_seeds(topic=req.topic, user_direction=req.direction, count=3)

    if not seeds:
        raise HTTPException(
            status_code=404,
            detail="No relevant seeds found in catalog.db. Please ingest reference articles first.",
        )

    archetype_enum = None
    for a in ArticleArchetype:
        if a.name == req.target_archetype or a.value == req.target_archetype:
            archetype_enum = a
            break

    planner = SynthesisPlanner(llm_client=llm)
    try:
        blueprint = await planner.plan_blueprint(
            topic=req.topic,
            direction=req.direction,
            seeds=seeds,
            archetype=archetype_enum,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blueprint planning failed: {e}")

    raw_dict = blueprint.model_dump()
    return BlueprintGenerateResponse(
        working_title=blueprint.working_title,
        core_thesis=blueprint.core_thesis,
        target_audience=blueprint.target_audience,
        hook_strategy=blueprint.hook_strategy,
        key_framework=blueprint.key_framework,
        outline_sections=[s.model_dump() for s in blueprint.outline_sections],
        selected_seed_ids=[s.doc_id for s in seeds],
        raw_blueprint=raw_dict,
    )


@router.post("/synthesize", response_model=DraftSynthesizeResponse)
async def synthesize_draft(req: DraftSynthesizeRequest):
    """Synthesize full-length draft from blueprint and distilled seeds."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    llm = LLMClient()
    if not llm.api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM API Key (GEMINI_API_KEY) is required to synthesize drafts.",
        )

    retriever = SeedRetriever(config=config, repo=repo)
    if req.selected_seed_ids:
        seeds = _build_seed_assignments(repo, req.selected_seed_ids, req.topic, req.direction)
    else:
        seeds = retriever.retrieve_seeds(topic=req.topic, user_direction=req.direction, count=3)

    archetype_enum = None
    for a in ArticleArchetype:
        if a.name == req.target_archetype or a.value == req.target_archetype:
            archetype_enum = a
            break

    blueprint_obj = None
    if req.blueprint:
        try:
            blueprint_obj = SynthesisBlueprint.model_validate(req.blueprint)
        except Exception:
            blueprint_obj = None

    synthesizer = ArticleSynthesizer(config=config, repo=repo, llm_client=llm)
    try:
        output_path, clean_text, final_blueprint, sheets = await synthesizer.synthesize(
            topic=req.topic,
            direction=req.direction,
            seeds=seeds,
            archetype=archetype_enum,
            blueprint=blueprint_obj,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft synthesis failed: {e}")

    # Extract title
    title = final_blueprint.working_title if final_blueprint else "제목 미정"
    for line in clean_text.splitlines():
        if line.strip().startswith("# "):
            title = line.strip().replace("# ", "").strip()
            break

    # Save to database
    creation_id = f"c_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    repo.save_draft_creation(
        creation_id=creation_id,
        topic=req.topic,
        direction=req.direction,
        target_archetype=req.target_archetype,
        seed_doc_ids=[s.doc_id for s in seeds],
        blueprint_json=json.dumps(final_blueprint.model_dump(), ensure_ascii=False) if final_blueprint else "{}",
        distilled_sheets_json=json.dumps([s.model_dump() for s in sheets], ensure_ascii=False) if sheets else "[]",
        ai_draft_text=clean_text,
        status="DRAFT",
    )

    return DraftSynthesizeResponse(
        title=title,
        content=clean_text,
        char_count=len(clean_text),
        topic=req.topic,
        direction=req.direction,
        seed_doc_ids=[s.doc_id for s in seeds],
        creation_id=creation_id,
    )
