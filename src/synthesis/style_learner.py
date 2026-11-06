"""Style Learner (v2.0): Analyzes Diff pairs between AI drafts and user finalized articles."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    STYLE_LEARNING_SYSTEM_PROMPT,
    STYLE_LEARNING_USER_PROMPT,
)
from src.models import UserStyleProfile
from src.storage.repository import StorageRepository


class StyleLearner:
    """Extracts and persists UserStyleProfile from finalized user creations."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        repo: Optional[StorageRepository] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.config = config or load_config()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.llm_client = llm_client or LLMClient()
        self.my_corpus_dir = self.config.paths.data_dir / "my_corpus"
        self.my_corpus_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.my_corpus_dir / "style_profile.json"

    def get_active_profile(self) -> Optional[UserStyleProfile]:
        """Load currently active UserStyleProfile if exists."""
        if not self.profile_path.exists():
            return None
        try:
            return UserStyleProfile.model_validate_json(
                self.profile_path.read_text(encoding="utf-8")
            )
        except Exception:
            return None

    def get_finalized_candidates(self, min_count: int = 5, force: bool = False) -> List[Dict[str, Any]]:
        """Fetch finalized creation records ready for style learning."""
        threshold = 1 if force else min_count
        return self.repo.get_finalized_creations_for_learning(min_count=threshold, include_already_used=True)

    def count_finalized_creations(self) -> int:
        """Count total finalized creations currently in DB."""
        creations = self.repo.list_creations(status="FINALIZED")
        return len(creations)

    def save_finalized_article(self, creation_id: str, title: str, content: str) -> Path:
        """Save finalized markdown article to data/my_corpus/."""
        import hashlib, re
        ascii_tokens = re.findall(r"[a-zA-Z0-9]+", title)
        prefix = "_".join(ascii_tokens)[:20].lower() if ascii_tokens else "article"
        hash_suffix = hashlib.sha256(title.encode("utf-8")).hexdigest()[:6]
        filename = f"{creation_id}_{prefix}_{hash_suffix}.md"
        dest_file = self.my_corpus_dir / filename
        dest_file.write_text(content, encoding="utf-8")
        return dest_file

    def _prepare_diff_payload(self, candidates: List[Dict[str, Any]]) -> str:
        """Format candidate pairs for LLM style extraction."""
        payload = []
        for c in candidates:
            payload.append({
                "creation_id": c["creation_id"],
                "topic": c["topic"],
                "ai_draft_before": c["ai_draft_text"][:3000],
                "user_final_after": c["user_final_text"][:3000],
                "user_notes": c.get("custom_notes", ""),
            })
        return json.dumps(payload, ensure_ascii=False, indent=2)

    async def learn_style(
        self,
        min_count: int = 5,
        force: bool = False,
    ) -> Optional[UserStyleProfile]:
        """Asynchronously analyze finalized creations and update style_profile.json."""
        candidates = self.get_finalized_candidates(min_count=min_count, force=force)
        if not candidates:
            return None

        diff_payload = self._prepare_diff_payload(candidates)
        user_prompt = STYLE_LEARNING_USER_PROMPT.format(
            count=len(candidates),
            diff_pairs_json=diff_payload,
        )

        profile = await self.llm_client.extract_structured(
            system_prompt=STYLE_LEARNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=UserStyleProfile,
        )

        profile.based_on_creation_count = len(candidates)
        self.profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

        # Mark as used in DB
        creation_ids = [c["creation_id"] for c in candidates]
        self.repo.mark_creations_used_for_style(creation_ids)

        # Log pipeline job
        now_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        job_id = f"style_{now_ts}"
        self.repo.create_job(job_id=job_id, job_type="STYLE_LEARNING", total_items=len(candidates))
        self.repo.update_job_progress(job_id=job_id, processed_delta=len(candidates), log_summary=f"Learned style from {len(candidates)} creations")
        self.repo.complete_job(job_id=job_id, status="COMPLETED", log_summary=f"Saved style profile v{profile.profile_version}")

        return profile

    def learn_style_sync(
        self,
        min_count: int = 5,
        force: bool = False,
    ) -> Optional[UserStyleProfile]:
        """Synchronous version for offline/sandbox mode."""
        candidates = self.get_finalized_candidates(min_count=min_count, force=force)
        if not candidates:
            return None

        diff_payload = self._prepare_diff_payload(candidates)
        user_prompt = STYLE_LEARNING_USER_PROMPT.format(
            count=len(candidates),
            diff_pairs_json=diff_payload,
        )

        profile = self.llm_client.extract_structured_sync(
            system_prompt=STYLE_LEARNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=UserStyleProfile,
        )

        profile.based_on_creation_count = len(candidates)
        self.profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

        creation_ids = [c["creation_id"] for c in candidates]
        self.repo.mark_creations_used_for_style(creation_ids)

        now_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        job_id = f"style_{now_ts}"
        self.repo.create_job(job_id=job_id, job_type="STYLE_LEARNING", total_items=len(candidates))
        self.repo.update_job_progress(job_id=job_id, processed_delta=len(candidates), log_summary=f"Learned style from {len(candidates)} creations")
        self.repo.complete_job(job_id=job_id, status="COMPLETED", log_summary=f"Saved style profile v{profile.profile_version}")

        return profile
