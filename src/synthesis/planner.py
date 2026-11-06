"""Blueprint planner: generates SynthesisBlueprint from selected Seed metadata."""

import json

from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    BLUEPRINT_GENERATION_SYSTEM_PROMPT,
    BLUEPRINT_GENERATION_USER_PROMPT,
)
from src.models import (
    ArticleArchetype,
    SeedRoleAssignment,
    SynthesisBlueprint,
)


class SynthesisPlanner:
    """Creates a unified SynthesisBlueprint from complementary seed metadata."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    async def plan_blueprint(
        self,
        topic: str,
        direction: str,
        seeds: list[SeedRoleAssignment],
        archetype: ArticleArchetype | None = None,
    ) -> SynthesisBlueprint:
        """Generate SynthesisBlueprint structured output."""
        seeds_summary_blocks = []
        for s in seeds:
            block = {
                "doc_id": s.doc_id,
                "role": s.seed_type,
                "title": s.title,
                "assignment_reason": s.reason,
                "target_audience": s.metadata.target_audience,
                "reframing_logic": s.metadata.reframing_logic,
                "core_thesis": s.metadata.core_thesis,
                "solution_framework": s.metadata.solution_framework,
                "notable_episodes": s.metadata.notable_episodes,
                "archetype": s.metadata.article_archetype.value,
            }
            seeds_summary_blocks.append(block)

        user_prompt = BLUEPRINT_GENERATION_USER_PROMPT.format(
            topic=topic,
            direction=direction or "실용적인 실행 방법론 제시",
            archetype=archetype.value if archetype else "시행착오 회고 및 실전 가이드",
            seeds_summary=json.dumps(seeds_summary_blocks, ensure_ascii=False, indent=2),
        )

        blueprint = await self.llm_client.extract_structured(
            system_prompt=BLUEPRINT_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=SynthesisBlueprint,
        )

        return blueprint

    def plan_blueprint_sync(
        self,
        topic: str,
        direction: str,
        seeds: list[SeedRoleAssignment],
        archetype: ArticleArchetype | None = None,
    ) -> SynthesisBlueprint:
        """Synchronous version for offline/sandbox mode."""
        seeds_summary_blocks = []
        for s in seeds:
            block = {
                "doc_id": s.doc_id,
                "role": s.seed_type,
                "title": s.title,
                "assignment_reason": s.reason,
                "target_audience": s.metadata.target_audience,
                "reframing_logic": s.metadata.reframing_logic,
                "core_thesis": s.metadata.core_thesis,
                "solution_framework": s.metadata.solution_framework,
                "notable_episodes": s.metadata.notable_episodes,
                "archetype": s.metadata.article_archetype.value,
            }
            seeds_summary_blocks.append(block)

        user_prompt = BLUEPRINT_GENERATION_USER_PROMPT.format(
            topic=topic,
            direction=direction or "실용적인 실행 방법론 제시",
            archetype=archetype.value if archetype else "시행착오 회고 및 실전 가이드",
            seeds_summary=json.dumps(seeds_summary_blocks, ensure_ascii=False, indent=2),
        )

        return self.llm_client.extract_structured_sync(
            system_prompt=BLUEPRINT_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=SynthesisBlueprint,
        )
