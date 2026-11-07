"""Draft Generation and Synthesis API router."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import verify_auth
from src.api.dependencies import (
    ConfigDep,
    RepoDep,
    build_article_detail,
    build_seed_assets_response,
)
from src.api.schemas.generator import (
    BlueprintGenerateRequest,
    BlueprintGenerateResponse,
    DraftSynthesizeRequest,
    DraftSynthesizeResponse,
    RandomInspirationRequest,
    RandomInspirationResponse,
    SeedAssetsResponse,
    SeedCandidateItem,
    SeedSearchRequest,
    SeedSearchResponse,
)
from src.extraction.llm_client import LLMClient
from src.models import ArticleArchetype, SeedRoleAssignment, SynthesisBlueprint
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.synthesis.inspirator import RandomIdeaInspirator
from src.synthesis.planner import SynthesisPlanner
from src.synthesis.synthesizer import ArticleSynthesizer

router = APIRouter(prefix="/draft", tags=["Draft Generation"], dependencies=[Depends(verify_auth)])


def _build_seed_assignments(
    repo: StorageRepository,
    selected_ids: list[str],
    topic: str,
    direction: str,
) -> list[SeedRoleAssignment]:
    """Build SeedRoleAssignment objects from explicitly selected doc_ids."""
    role_order = ["domain_case", "perspective_framework", "synthesis_counterpoint"]
    assignments: list[SeedRoleAssignment] = []

    for idx, did in enumerate(selected_ids):
        art = repo.get_article(did)
        meta = repo.get_article_metadata(did)
        if not art or not meta:
            continue
        role = role_order[idx] if idx < len(role_order) else "supporting_reference"
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
async def search_seed_candidates(req: SeedSearchRequest, repo: RepoDep, config: ConfigDep):
    """Search and rank relevant Seed articles for the given topic and direction."""
    retriever = SeedRetriever(config=config, repo=repo)

    # 1. Retrieve candidates
    candidates = retriever.search_candidates(topic=req.topic, direction=req.direction, top_k=req.limit)

    # 2. Get role recommendations
    try:
        recommended_seeds = retriever.retrieve_seeds(topic=req.topic, user_direction=req.direction, count=3)
        role_map = {s.doc_id: s.seed_type for s in recommended_seeds}
    except Exception:
        role_map = {}

    items: list[SeedCandidateItem] = []
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
async def generate_blueprint(req: BlueprintGenerateRequest, repo: RepoDep, config: ConfigDep):
    """Generate structured synthesis blueprint outline."""
    llm = LLMClient(model=req.model, repo=repo)
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
    sections = [
        s.model_dump() if hasattr(s, "model_dump") else s
        for s in blueprint.outline_sections
    ]
    return BlueprintGenerateResponse(
        working_title=blueprint.working_title,
        core_thesis=blueprint.core_thesis,
        target_audience=blueprint.target_audience,
        hook_strategy=blueprint.hook_strategy,
        key_framework=blueprint.key_framework,
        outline_sections=sections,
        selected_seed_ids=[s.doc_id for s in seeds],
        raw_blueprint=raw_dict,
    )


@router.post("/synthesize", response_model=DraftSynthesizeResponse)
async def synthesize_draft(req: DraftSynthesizeRequest, repo: RepoDep, config: ConfigDep):
    """Synthesize full-length draft from blueprint and distilled seeds."""
    llm = LLMClient(model=req.model, repo=repo)
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
    title = final_blueprint.working_title if (final_blueprint and hasattr(final_blueprint, "working_title")) else "제목 미정"
    for line in clean_text.splitlines():
        if line.strip().startswith("# "):
            title = line.strip().replace("# ", "").strip()
            break

    creation_id = synthesizer.last_creation_id or f"cr_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    return DraftSynthesizeResponse(
        title=title,
        content=clean_text,
        char_count=len(clean_text),
        topic=req.topic,
        direction=req.direction,
        seed_doc_ids=[s.doc_id for s in seeds],
        creation_id=creation_id,
    )


@router.post("/random-inspiration", response_model=RandomInspirationResponse)
async def get_random_inspiration(repo: RepoDep, config: ConfigDep, req: RandomInspirationRequest | None = None):
    """Discover complementary cross-domain seeds and synthesize an inspiring article topic."""
    chosen_model = req.model if req else None
    llm = LLMClient(model=chosen_model, repo=repo)
    if not llm.api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM API Key (GEMINI_API_KEY) is required to generate random inspirations.",
        )

    inspirator = RandomIdeaInspirator(config=config, repo=repo, llm_client=llm)
    preferred_cat = req.preferred_category if req else None
    count = req.count if req else 3

    try:
        res = await inspirator.generate_random_inspiration(preferred_category=preferred_cat, count=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"랜덤 영감 생성 중 오류가 발생했습니다: {e}")

    return RandomInspirationResponse(
        topic=res["topic"],
        direction=res["direction"],
        target_archetype=res.get("target_archetype", "PRACTICAL_GUIDE"),
        concept_summary=res.get("concept_summary", ""),
        selected_seeds=res.get("selected_seeds", []),
    )


@router.get("/assets", response_model=SeedAssetsResponse)
async def get_seed_assets(seed_ids: str, repo: RepoDep):
    """Fetch visual assets for given comma-separated seed doc IDs."""
    ids = [s.strip() for s in seed_ids.split(",") if s.strip()]
    return build_seed_assets_response(repo, ids)


@router.get("/seeds/{doc_id}")
async def get_seed_detail(doc_id: str, repo: RepoDep):
    """Fetch complete metadata, original text, and visual assets of a specific seed."""
    return build_article_detail(repo, doc_id)
