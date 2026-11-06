"""Cross-domain inspiration generator and random draft theme synthesizer."""

import json
import random
from typing import Any

from pydantic import BaseModel, Field

from src.api.schemas.generator import SeedCandidateItem
from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.models import ArticleMetadata, ArticleRecord
from src.storage.db import get_connection
from src.storage.repository import StorageRepository


class IdeaPlanningOutput(BaseModel):
    """Structured LLM output for synthesized article theme."""

    topic: str = Field(
        ...,
        description="독자의 시선을 사로잡고 지적 호기심을 자극하는 구체적인 아티클 제목/주제 (예: '완벽주의와 번아웃을 해킹하는 린(Lean) 업무 스프린트법')",
    )
    direction: str = Field(
        ...,
        description="이 글의 고유한 집필 관점 및 전개 방향 (2~3문장: 독자에게 전달할 독창적 통찰과 행동 지침)",
    )
    target_archetype: str = Field(
        default="PRACTICAL_GUIDE",
        description="PRACTICAL_GUIDE, FAILURE_RETROSPECTIVE, REFRAMING_ESSAY, INDUSTRY_DEEPDIVE 중 가장 적합한 1개",
    )
    concept_summary: str = Field(
        ...,
        description="선택된 지식 자산(시드)들이 결합되어 창출하는 새로운 시너지와 기획 의도 (1~2문장)",
    )


# Synergistic category pairing to create creative, high-impact cross-domain synthesis
CATEGORY_SYNERGY_PAIRS: list[tuple[str, str]] = [
    ("자기관리", "업무스킬"),        # 행동심리/루틴 x 업무 실행력
    ("마케팅/브랜딩", "서비스기획/AI"),  # 고객 설득/포지셔닝 x 프로덕트 설계
    ("커리어/이직", "업무스킬"),        # 경력 성장 x 핵심 역량/프로세스
    ("서비스기획/AI", "자기관리"),      # 기술 자동화 x 인간의 인지 부하 해소
    ("마케팅/브랜딩", "커리어/이직"),    # 브랜드 스토리텔링 x 퍼스널 브랜딩
    ("부업/수익화", "업무스킬"),        # 비즈니스 모델 x 린 실행력
    ("자기관리", "커리어/이직"),        # 멘탈/동기부여 x 지속가능한 성장
    ("마케팅/브랜딩", "업무스킬"),      # 메시지 전달 x 문서/커뮤니케이션
]

ROLE_DESCRIPTIONS = [
    ("domain_case", "현실 문제 제기 및 생생한 현장 사례"),
    ("perspective_framework", "통념을 뒤집는 관점 전환 및 실행 프레임워크"),
    ("synthesis_counterpoint", "실무 체크리스트 및 보완적 실전 도구"),
]


class RandomIdeaInspirator:
    """Discovers and synthesizes complementary seeds across disparate domains into fresh article topics."""

    def __init__(
        self,
        config: AppConfig | None = None,
        repo: StorageRepository | None = None,
        llm_client: LLMClient | None = None,
    ):
        self.config = config or load_config()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.llm_client = llm_client or LLMClient(repo=self.repo)

    def select_cross_domain_seeds(
        self,
        preferred_category: str | None = None,
        count: int = 3,
    ) -> list[tuple[ArticleRecord, ArticleMetadata, str, str]]:
        """
        Select 2~3 complementary seeds across different categories.
        Returns: list of (ArticleRecord, ArticleMetadata, assigned_role, role_description)
        """
        conn = get_connection(self.config.paths.db_path)
        recent_ids = self.repo.get_recently_used_seed_ids(days=7)

        category_seeds: dict[str, list[tuple[ArticleRecord, ArticleMetadata, float]]] = {}
        try:
            cur = conn.cursor()
            sql = """
            SELECT a.doc_id, m.primary_category, m.notable_episodes_json, m.solution_framework_json, m.core_thesis
            FROM articles a
            JOIN article_metadata m ON a.doc_id = m.doc_id
            WHERE a.status = 'INDEXED'
            """
            cur.execute(sql)
            rows = cur.fetchall()

            for r in rows:
                doc_id = r["doc_id"]
                cat = r["primary_category"]
                art = self.repo.get_article(doc_id)
                meta = self.repo.get_article_metadata(doc_id)
                if not art or not meta:
                    continue

                # Calculate richness score
                ep_cnt = len(meta.notable_episodes)
                fw_cnt = len(meta.solution_framework)
                thesis_len = len(meta.core_thesis)

                score = (ep_cnt * 2.0) + (fw_cnt * 1.5) + (min(100, thesis_len) / 20.0)
                if doc_id in recent_ids:
                    score -= 10.0  # Cooldown penalty

                if cat not in category_seeds:
                    category_seeds[cat] = []
                category_seeds[cat].append((art, meta, score))
        finally:
            conn.close()

        if not category_seeds:
            return []

        # Sort within each category by richness
        for cat in category_seeds:
            category_seeds[cat].sort(key=lambda x: x[2], reverse=True)

        # Decide categories to combine
        available_cats = [c for c, items in category_seeds.items() if len(items) > 0]
        if preferred_category and preferred_category in category_seeds:
            cat1 = preferred_category
            other_cats = [c for c in available_cats if c != cat1]
            cat2 = random.choice(other_cats) if other_cats else cat1
        else:
            # Pick a synergistic pair if available
            valid_pairs = [
                (c1, c2) for c1, c2 in CATEGORY_SYNERGY_PAIRS
                if c1 in category_seeds and c2 in category_seeds and category_seeds[c1] and category_seeds[c2]
            ]
            if valid_pairs:
                cat1, cat2 = random.choice(valid_pairs)
            else:
                cat1 = random.choice(available_cats)
                other_cats = [c for c in available_cats if c != cat1]
                cat2 = random.choice(other_cats) if other_cats else cat1

        # Pick seeds from selected categories
        selected: list[tuple[ArticleRecord, ArticleMetadata]] = []
        selected_ids: set[str] = set()

        def pick_from_category(cat: str, top_n: int = 6) -> tuple[ArticleRecord, ArticleMetadata] | None:
            candidates = [x for x in category_seeds.get(cat, []) if x[0].doc_id not in selected_ids]
            if not candidates:
                # Fallback to any remaining
                for c in available_cats:
                    sub = [x for x in category_seeds.get(c, []) if x[0].doc_id not in selected_ids]
                    if sub:
                        candidates = sub
                        break
            if not candidates:
                return None
            pool = candidates[:top_n]
            chosen = random.choice(pool)
            selected_ids.add(chosen[0].doc_id)
            return (chosen[0], chosen[1])

        # Seed 1 from cat1
        s1 = pick_from_category(cat1)
        if s1:
            selected.append(s1)

        # Seed 2 from cat2
        s2 = pick_from_category(cat2)
        if s2:
            selected.append(s2)

        # Seed 3 if count >= 3
        if count >= 3:
            # Pick from either cat1 or cat2, or a 3rd category
            third_cats = [c for c in available_cats if c not in (cat1, cat2)]
            cat3 = random.choice(third_cats) if third_cats else (cat1 if len(category_seeds.get(cat1, [])) > 2 else cat2)
            s3 = pick_from_category(cat3)
            if s3:
                selected.append(s3)

        # Assign roles to seeds
        result: list[tuple[ArticleRecord, ArticleMetadata, str, str]] = []
        for idx, (art, meta) in enumerate(selected):
            role_key, role_desc = ROLE_DESCRIPTIONS[idx % len(ROLE_DESCRIPTIONS)]
            result.append((art, meta, role_key, role_desc))

        return result

    async def generate_random_inspiration(
        self,
        preferred_category: str | None = None,
        count: int = 3,
    ) -> dict[str, Any]:
        """
        Generates a fresh article concept by discovering and synthesizing cross-domain seeds.
        """
        seeds_with_roles = self.select_cross_domain_seeds(preferred_category=preferred_category, count=count)
        if not seeds_with_roles:
            raise ValueError("데이터베이스에 유효한 색인 시드 문서가 부족합니다.")

        # Build seed candidate items for response
        candidate_items: list[SeedCandidateItem] = []
        seed_summaries = []

        for art, meta, role_key, role_desc in seeds_with_roles:
            archetype_val = meta.article_archetype.value if hasattr(meta.article_archetype, "value") else str(meta.article_archetype)
            item = SeedCandidateItem(
                doc_id=art.doc_id,
                title=art.title,
                archetype=archetype_val,
                target_audience=meta.target_audience,
                core_thesis=meta.core_thesis,
                solution_framework=meta.solution_framework,
                notable_episodes=meta.notable_episodes,
                topic_tags=meta.topic_tags,
                relevance_score=1.0,
                assigned_role=role_key,
            )
            candidate_items.append(item)

            seed_summaries.append({
                "doc_id": art.doc_id,
                "title": art.title,
                "category": meta.primary_category,
                "assigned_role": f"{role_key} ({role_desc})",
                "core_problem": meta.core_problem,
                "core_thesis": meta.core_thesis,
                "reframing_logic": meta.reframing_logic,
                "solution_framework": meta.solution_framework[:3],
                "notable_episodes": meta.notable_episodes[:2],
            })

        # LLM Synthesis Prompt
        system_prompt = (
            "당신은 탁월한 통찰력과 기획력을 가진 국내 정상급 인사이트 에디터이자 콘텐츠 디렉터입니다.\n"
            "주어진 2~3편의 지식 자산(Seeds)은 서로 다른 도메인에서 도출된 고유한 문제의식, 관점 전환, 실행 프레임워크를 담고 있습니다.\n"
            "이 시드들의 알맹이를 창의적으로 결합하여, 독자의 지적 호기심을 강하게 자극하고 실무에 즉시 적용할 수 있는 독창적인 새 아티클 아이디어를 기획하세요.\n"
            "교과서적이고 진부한 제목 대신, '무릎을 탁 치게 만드는' 명확하고 반전 있는 화두를 제시하세요."
        )

        user_prompt = (
            "다음은 데이터베이스에서 선별된 3편의 상호보완적 지식 자산(Seeds)입니다:\n\n"
            f"{json.dumps(seed_summaries, ensure_ascii=False, indent=2)}\n\n"
            "위 시드들을 융합하여 작성할 다음 항목을 도출해주세요:\n"
            "1. topic: 독자의 시선을 사로잡는 매력적인 타깃 주제/제목 (30~55자 내외, 화두와 솔루션이 명확히 드러남)\n"
            "2. direction: 집필 방향 및 나만의 고유 관점 메모 (3~4문장: 어떤 경험/문제의식에서 출발해 어떻게 통념을 뒤집고 어떤 실행 결론을 낼 것인가)\n"
            "3. target_archetype: 글의 성격에 가장 어울리는 아키타입 하나를 선택 ('PRACTICAL_GUIDE', 'FAILURE_RETROSPECTIVE', 'REFRAMING_ESSAY', 'INDUSTRY_DEEPDIVE')\n"
            "4. concept_summary: 이 조합이 독자에게 주는 핵심 차별점 및 가치 (1~2문장)"
        )

        try:
            planned = await self.llm_client.extract_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=IdeaPlanningOutput,
            )
            topic = planned.topic.strip().strip('"').strip("'")
            direction = planned.direction.strip()
            target_archetype = planned.target_archetype.strip()
            concept_summary = planned.concept_summary.strip()
        except Exception:
            # Fallback if LLM structured extraction fails
            first_seed = seeds_with_roles[0]
            second_seed = seeds_with_roles[1] if len(seeds_with_roles) > 1 else first_seed
            topic = f"{first_seed[1].primary_category}와 {second_seed[1].primary_category}의 교차점: {first_seed[0].title}에서 배운 새로운 통찰"
            direction = (
                f"{first_seed[1].core_thesis}라는 문제의식에서 출발하여, "
                f"{second_seed[1].reframing_logic}를 접목해 실행 가능한 새로운 돌파구를 제시합니다."
            )
            target_archetype = "PRACTICAL_GUIDE"
            concept_summary = f"{first_seed[0].title}의 현장 경험과 {second_seed[0].title}의 프레임워크를 유기적으로 엮은 실천형 에세이"

        return {
            "topic": topic,
            "direction": direction,
            "target_archetype": target_archetype,
            "concept_summary": concept_summary,
            "selected_seeds": candidate_items,
        }
