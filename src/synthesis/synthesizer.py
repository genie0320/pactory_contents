"""Draft synthesizer (v2.0): de-contextualized synthesis using DistilledMaterialSheets."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    DRAFT_SYNTHESIS_SYSTEM_PROMPT,
    DRAFT_SYNTHESIS_USER_PROMPT,
)
from src.models import (
    ArticleArchetype,
    DistilledMaterialSheet,
    SeedRoleAssignment,
    SynthesisBlueprint,
    UserStyleProfile,
)
from src.storage.repository import StorageRepository
from src.synthesis.distiller import MaterialDistiller
from src.synthesis.planner import SynthesisPlanner


class CleanYamlDumper(yaml.SafeDumper):
    pass


def _yaml_str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


CleanYamlDumper.add_representer(str, _yaml_str_representer)


def dump_clean_yaml(data: dict) -> str:
    """Dump YAML without 80-char line-wrapping or backslash escape sequences."""
    return yaml.dump(
        data,
        Dumper=CleanYamlDumper,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )


class ArticleSynthesizer:
    """Orchestrates Blueprint planning, material distillation, and neutral draft synthesis."""

    def __init__(
        self,
        config: AppConfig | None = None,
        repo: StorageRepository | None = None,
        llm_client: LLMClient | None = None,
        planner: SynthesisPlanner | None = None,
        distiller: MaterialDistiller | None = None,
    ):
        self.config = config or load_config()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.llm_client = llm_client or LLMClient()
        self.planner = planner or SynthesisPlanner(llm_client=self.llm_client)
        self.distiller = distiller or MaterialDistiller(repo=self.repo, llm_client=self.llm_client)
        self.outputs_dir = self.config.paths.outputs_dir
        self.drafts_dir = self.config.paths.data_dir / "drafts"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.last_creation_id: str = ""

    @staticmethod
    def slugify(text: str) -> str:
        """Create filesystem-safe ASCII slug."""
        import hashlib
        ascii_tokens = re.findall(r"[a-zA-Z0-9]+", text)
        prefix = "_".join(ascii_tokens)[:24].lower() if ascii_tokens else "draft"
        hash_suffix = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:8]
        return f"{prefix}_{hash_suffix}"

    async def synthesize(
        self,
        topic: str,
        direction: str,
        seeds: list[SeedRoleAssignment],
        archetype: ArticleArchetype | None = None,
        style_profile: UserStyleProfile | None = None,
        output_dir: Path | None = None,
        blueprint: SynthesisBlueprint | None = None,
        distilled_sheets: list[DistilledMaterialSheet] | None = None,
    ) -> tuple[Path, str, SynthesisBlueprint, list[DistilledMaterialSheet]]:
        """
        v2.0 3-Stage Synthesis Pipeline:
        1. Plan blueprint from metadata
        2. Distill pure facts and causal chains from seeds (Raw text is stripped!)
        3. Synthesize neutral draft (with optional UserStyleProfile)
        """
        out_dir = Path(output_dir) if output_dir else self.outputs_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Blueprint Planning (reuse if already provided)
        if blueprint is None:
            blueprint = await self.planner.plan_blueprint(
                topic=topic,
                direction=direction,
                seeds=seeds,
                archetype=archetype,
            )

        # 2. Material Distillation (Raw text is NEVER passed to final writer)
        if distilled_sheets is None:
            distilled_sheets = await self.distiller.distill_all(seeds)

        # 3. Call LLM for neutral/styled synthesis
        style_guide_text = (
            style_profile.model_dump_json(indent=2)
            if style_profile
            else "기본 중립 모드: 과장된 수사나 상투적 요약 박스를 배제하고 담백하고 구조적인 표준 아티클로 집필할 것."
        )

        user_prompt = DRAFT_SYNTHESIS_USER_PROMPT.format(
            topic=topic,
            direction=direction or "실용적인 관점 전환 및 실행 방안 제시",
            blueprint_json=blueprint.model_dump_json(indent=2),
            distilled_sheets_json=json.dumps(
                [s.model_dump() for s in distilled_sheets], ensure_ascii=False, indent=2
            ),
            style_profile_json=style_guide_text,
        )

        draft_content = await self.llm_client.generate_text(
            system_prompt=DRAFT_SYNTHESIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # 4. Frontmatter
        now_utc = datetime.now(UTC)
        frontmatter_data = {
            "title": blueprint.proposed_title,
            "topic": topic,
            "direction": direction,
            "archetype": archetype.value if archetype else "custom",
            "style_profile_applied": style_profile is not None,
            "generated_at": now_utc.isoformat(),
            "seeds_used": [
                {
                    "doc_id": s.doc_id,
                    "title": s.title,
                    "role": s.seed_type,
                }
                for s in seeds
            ],
            "synthesized_reframing": blueprint.synthesized_reframing,
        }

        final_body = draft_content
        if draft_content.strip().startswith("---"):
            parts = draft_content.strip().split("---", 2)
            if len(parts) >= 3:
                final_body = parts[2].strip()

        yaml_str = dump_clean_yaml(frontmatter_data)
        final_markdown = f"---\n{yaml_str}---\n\n{final_body}\n"

        # 5. Output file (Single Source of Truth in outputs_dir)
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
        creation_id = f"cr_{timestamp_str}"
        self.last_creation_id = creation_id
        topic_slug = self.slugify(topic)
        output_file = out_dir / f"{creation_id}_{topic_slug}.md"
        output_file.write_text(final_markdown, encoding="utf-8")

        # 6. Save creation record to drafts_and_creations table
        self.repo.save_draft_creation(
            creation_id=creation_id,
            topic=topic,
            direction=direction,
            target_archetype=archetype.value if archetype else "custom",
            seed_doc_ids=[s.doc_id for s in seeds],
            blueprint_json=blueprint.model_dump_json(indent=2),
            distilled_sheets_json=json.dumps(
                [s.model_dump() for s in distilled_sheets], ensure_ascii=False, indent=2
            ),
            ai_draft_text=final_markdown,
            status="DRAFT",
        )

        # 7. Log synthesis job
        synth_job_id = f"synth_{timestamp_str}"
        self.repo.create_job(job_id=synth_job_id, job_type="DRAFT_SYNTHESIS", total_items=1)
        self.repo.update_job_progress(job_id=synth_job_id, processed_delta=1, log_summary=f"Synthesized draft {creation_id}")
        self.repo.complete_job(job_id=synth_job_id, status="COMPLETED", log_summary=f"Created {creation_id} for '{topic}'")

        return output_file, final_markdown, blueprint, distilled_sheets

    def synthesize_sync(
        self,
        topic: str,
        direction: str,
        seeds: list[SeedRoleAssignment],
        archetype: ArticleArchetype | None = None,
        style_profile: UserStyleProfile | None = None,
        output_dir: Path | None = None,
        blueprint: SynthesisBlueprint | None = None,
        distilled_sheets: list[DistilledMaterialSheet] | None = None,
    ) -> tuple[Path, str, SynthesisBlueprint, list[DistilledMaterialSheet]]:
        """Synchronous version for offline/sandbox mode."""
        out_dir = Path(output_dir) if output_dir else self.outputs_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Blueprint Planning (reuse if already provided)
        if blueprint is None:
            blueprint = self.planner.plan_blueprint_sync(
                topic=topic,
                direction=direction,
                seeds=seeds,
                archetype=archetype,
            )

        # 2. Material Distillation (reuse if already provided)
        if distilled_sheets is None:
            distilled_sheets = self.distiller.distill_all_sync(seeds)

        # 3. Call LLM for neutral/styled synthesis
        style_guide_text = (
            style_profile.model_dump_json(indent=2)
            if style_profile
            else "기본 중립 모드: 과장된 수사나 상투적 요약 박스를 배제하고 담백하고 구조적인 표준 아티클로 집필할 것."
        )

        user_prompt = DRAFT_SYNTHESIS_USER_PROMPT.format(
            topic=topic,
            direction=direction or "실용적인 관점 전환 및 실행 방안 제시",
            blueprint_json=blueprint.model_dump_json(indent=2),
            distilled_sheets_json=json.dumps(
                [s.model_dump() for s in distilled_sheets], ensure_ascii=False, indent=2
            ),
            style_profile_json=style_guide_text,
        )

        draft_content = self.llm_client.generate_text_sync(
            system_prompt=DRAFT_SYNTHESIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # 4. Frontmatter
        now_utc = datetime.now(UTC)
        frontmatter_data = {
            "title": blueprint.proposed_title,
            "topic": topic,
            "direction": direction,
            "archetype": archetype.value if archetype else "custom",
            "style_profile_applied": style_profile is not None,
            "generated_at": now_utc.isoformat(),
            "seeds_used": [
                {
                    "doc_id": s.doc_id,
                    "title": s.title,
                    "role": s.seed_type,
                }
                for s in seeds
            ],
            "synthesized_reframing": blueprint.synthesized_reframing,
        }

        final_body = draft_content
        if draft_content.strip().startswith("---"):
            parts = draft_content.strip().split("---", 2)
            if len(parts) >= 3:
                final_body = parts[2].strip()

        yaml_str = dump_clean_yaml(frontmatter_data)
        final_markdown = f"---\n{yaml_str}---\n\n{final_body}\n"

        # 5. Output file (Single Source of Truth in outputs_dir)
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
        creation_id = f"cr_{timestamp_str}"
        self.last_creation_id = creation_id
        topic_slug = self.slugify(topic)
        output_file = out_dir / f"{creation_id}_{topic_slug}.md"
        output_file.write_text(final_markdown, encoding="utf-8")

        # 6. Save creation record to drafts_and_creations table
        self.repo.save_draft_creation(
            creation_id=creation_id,
            topic=topic,
            direction=direction,
            target_archetype=archetype.value if archetype else "custom",
            seed_doc_ids=[s.doc_id for s in seeds],
            blueprint_json=blueprint.model_dump_json(indent=2),
            distilled_sheets_json=json.dumps(
                [s.model_dump() for s in distilled_sheets], ensure_ascii=False, indent=2
            ),
            ai_draft_text=final_markdown,
            status="DRAFT",
        )

        # 7. Log synthesis job
        synth_job_id = f"synth_{timestamp_str}"
        self.repo.create_job(job_id=synth_job_id, job_type="DRAFT_SYNTHESIS", total_items=1)
        self.repo.update_job_progress(job_id=synth_job_id, processed_delta=1, log_summary=f"Synthesized draft {creation_id}")
        self.repo.complete_job(job_id=synth_job_id, status="COMPLETED", log_summary=f"Created {creation_id} for '{topic}'")

        return output_file, final_markdown, blueprint, distilled_sheets
