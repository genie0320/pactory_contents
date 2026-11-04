"""Material distiller: strips style and rhetoric from Seed articles into pure fact sheets."""

from typing import List, Optional
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    MATERIAL_DISTILLATION_SYSTEM_PROMPT,
    MATERIAL_DISTILLATION_USER_PROMPT,
)
from src.models import DistilledMaterialSheet, SeedRoleAssignment
from src.storage.repository import StorageRepository


class MaterialDistiller:
    """Distills raw text into de-contextualized, bulleted fact & mechanism sheets."""

    def __init__(
        self,
        repo: Optional[StorageRepository] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.repo = repo
        self.llm_client = llm_client or LLMClient()

    async def distill_seed(
        self,
        seed: SeedRoleAssignment,
    ) -> DistilledMaterialSheet:
        """Distill a single seed article into DistilledMaterialSheet."""
        raw_text = ""
        if self.repo:
            try:
                raw_text = self.repo.get_processed_text(seed.doc_id)
            except Exception:
                raw_text = ""

        user_prompt = MATERIAL_DISTILLATION_USER_PROMPT.format(
            doc_id=seed.doc_id,
            assigned_role=seed.seed_type,
            raw_text=raw_text[:12000],
        )

        sheet = await self.llm_client.extract_structured(
            system_prompt=MATERIAL_DISTILLATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=DistilledMaterialSheet,
        )
        return sheet

    def distill_seed_sync(
        self,
        seed: SeedRoleAssignment,
    ) -> DistilledMaterialSheet:
        """Synchronous distillation for offline/sandbox mode."""
        raw_text = ""
        if self.repo:
            try:
                raw_text = self.repo.get_processed_text(seed.doc_id)
            except Exception:
                raw_text = ""

        user_prompt = MATERIAL_DISTILLATION_USER_PROMPT.format(
            doc_id=seed.doc_id,
            assigned_role=seed.seed_type,
            raw_text=raw_text[:12000],
        )

        sheet = self.llm_client.extract_structured_sync(
            system_prompt=MATERIAL_DISTILLATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=DistilledMaterialSheet,
        )
        return sheet

    async def distill_all(
        self,
        seeds: List[SeedRoleAssignment],
    ) -> List[DistilledMaterialSheet]:
        """Distill all selected seeds asynchronously."""
        sheets: List[DistilledMaterialSheet] = []
        for s in seeds:
            sheet = await self.distill_seed(s)
            sheets.append(sheet)
        return sheets

    def distill_all_sync(
        self,
        seeds: List[SeedRoleAssignment],
    ) -> List[DistilledMaterialSheet]:
        """Distill all selected seeds synchronously."""
        sheets: List[DistilledMaterialSheet] = []
        for s in seeds:
            sheet = self.distill_seed_sync(s)
            sheets.append(sheet)
        return sheets
