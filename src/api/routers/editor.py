"""Studio Editor, Creations, and Proofreading API router."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.auth import verify_auth
from src.api.dependencies import ConfigDep, RepoDep, build_seed_assets_response
from src.api.schemas.editor import (
    CreationDetailResponse,
    CreationSaveRequest,
    CreationSummaryItem,
    CreationUpdateRequest,
    ProofreadRequest,
    ProofreadResponse,
)
from src.api.schemas.generator import SeedAssetsResponse
from src.exceptions import LLMServiceError
from src.extraction.llm_client import LLMClient
from src.synthesis.proofreader import ArticleProofreader

router = APIRouter(tags=["Editor & Creations"], dependencies=[Depends(verify_auth)])


def _extract_title_from_text(text: str) -> str:
    for line in text.splitlines():
        line_str = line.strip()
        if line_str.startswith("# "):
            return line_str.replace("# ", "").strip()
    return "제목 미정"


# -------------------------------------------------------------
# Creations CRUD
# -------------------------------------------------------------
@router.get("/creations", response_model=list[CreationSummaryItem])
async def list_creations(
    repo: RepoDep,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
):
    """List all draft and finalized creations."""
    records = repo.list_creations(status=status_filter, limit=limit)

    items: list[CreationSummaryItem] = []
    for r in records:
        text_for_title = r.get("user_final_text") or r.get("ai_draft_text") or ""
        items.append(
            CreationSummaryItem(
                creation_id=r["creation_id"],
                topic=r.get("topic", "주제 미정"),
                direction=r.get("direction", ""),
                target_archetype=r.get("target_archetype", "PRACTICAL_GUIDE"),
                status=r.get("status", "DRAFT"),
                created_at=r.get("created_at", ""),
                finalized_at=r.get("finalized_at"),
                has_final=bool(r.get("user_final_text")),
                title=_extract_title_from_text(text_for_title),
                seed_doc_ids=r.get("seed_doc_ids", []),
            )
        )
    return items


@router.get("/creations/{creation_id}", response_model=CreationDetailResponse)
async def get_creation(creation_id: str, repo: RepoDep):
    """Retrieve full creation details including AI draft and user final revisions."""
    rec = repo.get_creation(creation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creation '{creation_id}' not found.",
        )

    return CreationDetailResponse(
        creation_id=rec["creation_id"],
        topic=rec.get("topic", ""),
        direction=rec.get("direction", ""),
        target_archetype=rec.get("target_archetype", "PRACTICAL_GUIDE"),
        ai_draft_text=rec.get("ai_draft_text", ""),
        user_final_text=rec.get("user_final_text", ""),
        custom_notes=rec.get("custom_notes", ""),
        status=rec.get("status", "DRAFT"),
        seed_doc_ids=rec.get("seed_doc_ids", []),
        created_at=rec.get("created_at", ""),
        finalized_at=rec.get("finalized_at"),
    )


@router.post("/creations", response_model=CreationDetailResponse)
async def save_creation(req: CreationSaveRequest, repo: RepoDep):
    """Save a new creation record."""
    creation_id = f"c_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    repo.save_draft_creation(
        creation_id=creation_id,
        topic=req.topic,
        direction=req.direction,
        target_archetype=req.target_archetype,
        seed_doc_ids=req.seed_doc_ids,
        blueprint_json=req.blueprint_json,
        distilled_sheets_json=req.distilled_sheets_json,
        ai_draft_text=req.ai_draft_text,
        status=req.status,
    )

    rec = repo.get_creation(creation_id)
    return CreationDetailResponse(
        creation_id=creation_id,
        topic=req.topic,
        direction=req.direction,
        target_archetype=req.target_archetype,
        ai_draft_text=req.ai_draft_text,
        user_final_text="",
        custom_notes="",
        status=req.status,
        seed_doc_ids=req.seed_doc_ids,
        created_at=rec.get("created_at", "") if rec else "",
    )


@router.put("/creations/{creation_id}", response_model=CreationDetailResponse)
async def update_creation(creation_id: str, req: CreationUpdateRequest, repo: RepoDep, config: ConfigDep):
    """Update finalized text, editorial notes, or status of an existing creation."""
    rec = repo.get_creation(creation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creation '{creation_id}' not found.",
        )

    repo.update_creation_final(
        creation_id=creation_id,
        user_final_text=req.user_final_text,
        custom_notes=req.custom_notes,
        status=req.status,
    )

    # Clean up duplicate older DRAFT records for the same topic upon finalization
    if req.status == "FINALIZED" and rec.get("topic"):
        repo.cleanup_older_drafts(topic=rec["topic"], keep_creation_id=creation_id)

    # Policy 4: Dual-Write real-time synchronization between DB and filesystem (SSOT)
    if req.user_final_text:
        repo.sync_creation_to_outputs(
            outputs_dir=config.paths.outputs_dir,
            creation_id=creation_id,
            topic=rec.get("topic") or "draft",
            text=req.user_final_text,
        )

    updated = repo.get_creation(creation_id)
    return CreationDetailResponse(
        creation_id=creation_id,
        topic=updated.get("topic", ""),
        direction=updated.get("direction", ""),
        target_archetype=updated.get("target_archetype", "PRACTICAL_GUIDE"),
        ai_draft_text=updated.get("ai_draft_text", ""),
        user_final_text=updated.get("user_final_text", ""),
        custom_notes=updated.get("custom_notes", ""),
        status=updated.get("status", "FINALIZED"),
        seed_doc_ids=updated.get("seed_doc_ids", []),
        created_at=updated.get("created_at", ""),
        finalized_at=updated.get("finalized_at"),
    )


@router.delete("/creations/{creation_id}")
async def delete_creation(creation_id: str, repo: RepoDep):
    """Delete a creation record."""
    deleted = repo.delete_creation(creation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creation '{creation_id}' not found.",
        )
    return {"success": True, "message": f"Creation '{creation_id}' successfully deleted."}


# -------------------------------------------------------------
# Proofreading & Platform Rewriting
# -------------------------------------------------------------
@router.post("/proofread", response_model=ProofreadResponse)
async def proofread_draft(req: ProofreadRequest):
    """Perform editorial critique or platform-tailored rewrite via LLM."""
    llm = LLMClient(model=req.model)
    if not llm.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API Key (GEMINI_API_KEY) is required for proofreading and rewriting.",
        )

    proofreader = ArticleProofreader(llm_client=llm)
    try:
        res = await proofreader.review(
            content=req.content,
            platform=req.platform,
            mode=req.mode,
            custom_instruction=req.custom_instruction,
            critique_feedback=req.critique_feedback,
            metadata_context=req.metadata_context,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Proofreading failed: {e}")

    return ProofreadResponse(
        platform=res["platform"],
        mode=res["mode"],
        critique_report=res.get("critique_report") or "",
        rewritten_text=res.get("rewritten_text"),
        hooking_score=res.get("hooking_score", 9),
        balance_score=res.get("balance_score", 9),
        platform_score=res.get("platform_score", 9),
        suggested_title=res.get("suggested_title", "제목 미정"),
    )


@router.get("/creations/{creation_id}/assets", response_model=SeedAssetsResponse)
async def get_creation_assets(creation_id: str, repo: RepoDep):
    """Fetch visual assets for all seeds utilized in the given creation."""
    creation = repo.get_creation(creation_id)
    if not creation:
        raise HTTPException(status_code=404, detail="Creation record not found")

    seed_ids = creation.get("seed_doc_ids") or []
    return build_seed_assets_response(repo, seed_ids)
