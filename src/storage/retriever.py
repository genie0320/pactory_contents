"""Cross-seed retrieval and role-based complementary ranking engine."""

import json
import logging
import math
import re
from typing import Any

from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ArticleRecord,
    ReusableAssetType,
    SeedRoleAssignment,
)
from src.storage.db import get_connection
from src.storage.repository import StorageRepository

logger = logging.getLogger(__name__)

# Common Korean functional words and discourse markers to ignore in retrieval
KOREAN_STOPWORDS: set[str] = {
    "흔히", "통해", "과정", "있어야", "있으면", "하고", "만큼", "한다", "생각", "위해",
    "대한", "모든", "다른", "때문", "어떤", "이런", "저런", "그런", "매우", "가장",
    "더욱", "아주", "전혀", "단순", "것이", "경우", "관련", "대해", "이유", "방법",
    "정말", "바로", "다시", "하나", "두개", "세개", "포함", "내용", "사람", "자신",
    "우리", "그들", "어떻게", "무엇", "언제", "어디", "왜냐하면", "하지만", "그리고",
    "따라서", "그래서", "그래서요", "중요해요", "착안했다고", "아무런", "쓸모", "없으며",
    "타인에게", "설명할", "다듬고", "깍는", "거칠", "있을", "표현될", "표현되지", "못한",
    "지나가", "좋은", "일뿐", "뿐이다", "수도", "있는", "없는", "되는", "하는", "이다",
    "아니다", "그냥", "단지", "약간", "조금", "항상", "자주", "가끔",
    # Additional functional and noise words identified in benchmark audit
    "아닌", "아니", "것은", "것을", "가지고", "가진", "위한", "관한", "소위", "가깝다",
    "본다면", "그것", "얼마든지", "원하", "뒤집", "있기때문", "부르", "세기적인", "태어난",
    "이러한", "저러한", "그러한", "통하여", "대하여", "위하여", "인하여", "말한다", "보인다",
}

# Domain synonym expansion is deprecated in favor of Index-time LLM 10-Keyword Enrichment
DOMAIN_SYNONYMS: dict[str, list[str]] = {}


class SeedRetriever:
    """Retrieves and ranks complementary Seed articles based on Hybrid FTS5 BM25 + Dense Vectors."""

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
        self.db_path = self.config.paths.db_path
        self.llm_client = llm_client or LLMClient(repo=self.repo)

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two dense vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 <= 0.0 or norm2 <= 0.0:
            return 0.0
        return dot / (norm1 * norm2)

    @staticmethod
    def extract_keywords(text: str) -> list[str]:
        """Extract meaningful keywords stripping Korean particles, predicate endings, and punctuation."""
        cleaned = re.sub(r"[^\w\s가-힣a-zA-Z0-9]", " ", text)
        tokens = cleaned.split()
        particles = (
            "이라는", "이라고", "에서는", "으로는", "이나", "에서", "으로", "부터", "까지",
            "보다", "에게", "하고", "은", "는", "이", "가", "을", "를", "의", "에", "로",
            "와", "과", "도"
        )
        endings = (
            "때문이다", "기때문", "있기때문", "한다는", "된다는", "으로는", "해보세요",
            "했어요", "해요", "어요", "다고", "으면", "어서", "지만", "었다", "했다",
            "한다", "된다", "이다", "이며"
        )
        keywords: list[str] = []
        for t in tokens:
            t_clean = t.strip()
            if len(t_clean) <= 1 or t_clean in KOREAN_STOPWORDS:
                continue
            for p in particles:
                if t_clean.endswith(p) and len(t_clean) > len(p) + 1:
                    t_clean = t_clean[: -len(p)]
                    break
            for e in endings:
                if t_clean.endswith(e) and len(t_clean) > len(e) + 1:
                    t_clean = t_clean[: -len(e)]
                    break
            if len(t_clean) >= 2 and t_clean not in KOREAN_STOPWORDS:
                keywords.append(t_clean)
        return list(dict.fromkeys(keywords))

    @staticmethod
    def jaccard_similarity(tags1: list[str], tags2: list[str]) -> float:
        """Compute Jaccard similarity between two tag lists."""
        s1 = set(t.lower() for t in tags1)
        s2 = set(t.lower() for t in tags2)
        if not s1 or not s2:
            return 0.0
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        return intersection / float(union) if union > 0 else 0.0

    def search_candidates(
        self,
        topic: str,
        direction: str = "",
        top_k: int = 15,
        alpha: float = 0.5,
    ) -> list[tuple[ArticleRecord, ArticleMetadata, float]]:
        """
        Hybrid retrieval combining FTS5 BM25 (keyword matching) and Dense Vector Embedding (semantic similarity).
        Final score:
            score = (alpha * normalized_bm25) + ((1.0 - alpha) * vector_similarity)
        """
        topic_keywords = self.extract_keywords(topic)
        direction_keywords = self.extract_keywords(direction) if direction else []
        all_keywords = (topic_keywords * 3) + direction_keywords

        if not all_keywords:
            all_keywords = [topic.strip()]

        fts_query = " OR ".join(f'"{kw}"' for kw in all_keywords if kw)
        conn = get_connection(self.db_path)
        candidates: list[tuple[ArticleRecord, ArticleMetadata, float]] = []
        seen_doc_ids: set[str] = set()

        try:
            cursor = conn.cursor()
            if fts_query:
                sql = """
                SELECT doc_id, bm25(metadata_fts, 3.0, 1.0, 1.0, 1.5, 2.0, 2.0, 1.5, 1.5, 4.0, 1.0) as rank
                FROM metadata_fts
                WHERE metadata_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """
                cursor.execute(sql, (fts_query, top_k * 2))
                for row in cursor.fetchall():
                    did = row["doc_id"]
                    rank = float(row["rank"])
                    if did not in seen_doc_ids:
                        art = self.repo.get_article(did)
                        meta = self.repo.get_article_metadata(did)
                        if art and meta:
                            candidates.append((art, meta, rank))
                            seen_doc_ids.add(did)

            # Fallback search if candidates < top_k
            if len(candidates) < top_k:
                fallback_limit = top_k - len(candidates)
                like_clauses = []
                params: list[Any] = []
                for kw in all_keywords[:3]:
                    like_clauses.append("(topic_tags_json LIKE ? OR primary_category LIKE ?)")
                    params.extend([f"%{kw}%", f"%{kw}%"])

                if like_clauses:
                    where_sql = " OR ".join(like_clauses)
                    sql_fb = f"SELECT doc_id FROM article_metadata WHERE {where_sql} LIMIT ?"
                    params.append(fallback_limit * 2)
                    cursor.execute(sql_fb, params)
                    for row in cursor.fetchall():
                        did = row["doc_id"]
                        if did not in seen_doc_ids:
                            art = self.repo.get_article(did)
                            meta = self.repo.get_article_metadata(did)
                            if art and meta:
                                candidates.append((art, meta, 0.0))  # fallback score
                                seen_doc_ids.add(did)

            # If candidates are still fewer than top_k, fill from available indexed articles
            if len(candidates) < top_k:
                fill_limit = top_k - len(candidates)
                if seen_doc_ids:
                    placeholders = ",".join("?" for _ in seen_doc_ids)
                    sql_fill = f"SELECT doc_id FROM articles WHERE status = 'INDEXED' AND doc_id NOT IN ({placeholders}) LIMIT ?"
                    params_fill = list(seen_doc_ids) + [fill_limit]
                else:
                    sql_fill = "SELECT doc_id FROM articles WHERE status = 'INDEXED' LIMIT ?"
                    params_fill = [fill_limit]

                cursor.execute(sql_fill, params_fill)
                for row in cursor.fetchall():
                    did = row["doc_id"]
                    if did not in seen_doc_ids:
                        art = self.repo.get_article(did)
                        meta = self.repo.get_article_metadata(did)
                        if art and meta:
                            candidates.append((art, meta, 0.0))
                            seen_doc_ids.add(did)

        finally:
            conn.close()

        # Cooldown check: penalize seeds used in creations within the last 7 days
        recent_seed_ids = self.repo.get_recently_used_seed_ids(days=7)

        # Dense Vector Re-ranking & Hybrid Fusion
        try:
            query_text = f"{topic} {direction}".strip()
            query_vec = self.llm_client.get_embedding_sync(query_text)
            stored_embeddings = self.repo.get_all_embeddings()

            hybrid_candidates = []
            for art, meta, raw_rank in candidates:
                norm_bm25 = abs(raw_rank) / (1.0 + abs(raw_rank)) if raw_rank != 0.0 else 0.0
                art_vec = stored_embeddings.get(art.doc_id)
                if not art_vec or len(art_vec) != len(query_vec):
                    doc_repr = f"{art.title}. {meta.core_thesis}. {' '.join(meta.topic_tags)}"
                    art_vec = self.llm_client.get_embedding_sync(doc_repr)
                    self.repo.upsert_article_embedding(art.doc_id, art_vec)
                    stored_embeddings[art.doc_id] = art_vec

                sim = self.cosine_similarity(query_vec, art_vec)
                norm_sim = max(0.0, sim)
                final_score = (alpha * norm_bm25) + ((1.0 - alpha) * norm_sim)

                # Policy 3: Apply 25% cooldown penalty to recently adopted seeds
                if art.doc_id in recent_seed_ids:
                    final_score *= 0.75

                hybrid_candidates.append((art, meta, round(final_score, 4)))

            hybrid_candidates.sort(key=lambda x: x[2], reverse=True)
            return hybrid_candidates[:top_k]
        except Exception:
            # Fallback ranking if vector ranking fails: correctly normalize BM25
            norm_candidates = []
            for art, meta, raw_rank in candidates:
                norm_bm25 = abs(raw_rank) / (1.0 + abs(raw_rank)) if raw_rank != 0.0 else 0.0
                if art.doc_id in recent_seed_ids:
                    norm_bm25 *= 0.75
                norm_candidates.append((art, meta, round(norm_bm25, 4)))
            norm_candidates.sort(key=lambda x: x[2], reverse=True)
            return norm_candidates[:top_k]

    def retrieve_seeds(
        self,
        topic: str,
        user_direction: str = "",
        target_archetype: ArticleArchetype | None = None,
        count: int = 3,
        use_llm: bool = True,
    ) -> list[SeedRoleAssignment]:
        """
        Two-stage Seed Retrieval:
        1. If LLM is available and use_llm=True, perform Stage 2 LLM Contextual Curation.
        2. Fall back to bug-fixed deterministic hybrid ranking if LLM fails or is disabled.
        """
        if use_llm and self.llm_client and self.llm_client.api_key:
            try:
                curated = self.llm_curate_seeds(
                    topic=topic,
                    direction=user_direction,
                    target_archetype=target_archetype,
                    count=count,
                )
                if curated and len(curated) >= count:
                    return curated
            except Exception as e:
                logger.warning(f"LLM curation failed, falling back to hybrid ranking: {e}")

        return self.select_complementary_seeds(
            topic=topic,
            direction=user_direction,
            target_archetype=target_archetype,
            count=count,
        )

    def llm_curate_seeds(
        self,
        topic: str,
        direction: str = "",
        target_archetype: ArticleArchetype | None = None,
        count: int = 3,
    ) -> list[SeedRoleAssignment]:
        """
        Stage 2: LLM Contextual Reasoning & Role Curation.
        Evaluates top hybrid candidates against the user's specific thesis, nuance, and direction.
        """
        candidates = self.search_candidates(topic=topic, direction=direction, top_k=25, alpha=0.4)
        if not candidates:
            return []

        cand_map = {}
        candidate_items = []
        for art, meta, score in candidates:
            cand_map[art.doc_id] = (art, meta)
            candidate_items.append({
                "doc_id": art.doc_id,
                "title": art.title,
                "category": meta.primary_category,
                "archetype": meta.article_archetype.value if hasattr(meta.article_archetype, "value") else str(meta.article_archetype),
                "core_thesis": meta.core_thesis,
                "tags": meta.topic_tags[:5],
                "episodes_sample": meta.notable_episodes[:2],
                "solution_framework": meta.solution_framework[:3],
                "retrieval_score": score,
            })

        system_prompt = """당신은 수석 콘텐츠 큐레이터이자 편집장입니다.
사용자가 작성하려는 아티클의 [주제]와 [집필 방향]에 가장 완벽하게 부합하고 상호 보완적인 3편의 Seed 아티클을 엄선하세요.

[선별 원칙 - 3대 역할 분담]
1. domain_case (도메인 사례/팩트):
   - 사용자의 주제와 직결되는 생생한 현장 사례, 인물, 데이터.
   - 단어 몇 개만 우연히 겹친 무관한 글(예: 버거 탐방기, 엉뚱한 해외 여행기 등)은 엄격히 배제하세요.
2. perspective_framework (관점 전환 & 논리):
   - 상식을 뒤흔드는 통념 반박(Reframing)과 깊이 있는 분석 논리, 3~4단계 해결 프레임워크를 제공하는 글.
3. structure_asset (실천 도구 & 구조):
   - 독자가 즉시 실행할 수 있는 실무 체크리스트, 템플릿, 프롬프트, 구체적 훈련법을 제공하는 글.

[반환 형식]
반드시 아래 JSON 형식으로만 응답하세요:
[
  {
    "doc_id": "문서 ID",
    "title": "제목",
    "seed_type": "domain_case|perspective_framework|structure_asset",
    "reason": "선정 이유 (사용자 주제와의 구체적 접점 설명)"
  }, ...
]"""

        user_prompt = f"""[사용자 집필 의도]
- 타깃 주제 (Topic): {topic}
- 집필 방향 및 고유 관점 (Direction): {direction}

[검색된 1차 후보 아티클 목록 (총 {len(candidate_items)}편)]:
{json.dumps(candidate_items, ensure_ascii=False, indent=2)}

위 후보 중에서 가장 완벽한 3편의 조합을 선정하여 JSON으로 응답하세요."""

        resp_text = self.llm_client.generate_text_sync(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type="intelligent_seed_curation",
        )
        clean_text = resp_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
        clean_text = clean_text.strip()
        curated_raw = json.loads(clean_text)

        selected: list[SeedRoleAssignment] = []
        for item in curated_raw[:count]:
            did = str(item.get("doc_id", ""))
            if did in cand_map:
                art, meta = cand_map[did]
                selected.append(
                    SeedRoleAssignment(
                        seed_type=item.get("seed_type", "domain_case"),
                        doc_id=art.doc_id,
                        title=art.title,
                        reason=item.get("reason", f"주제({topic})와의 적합성"),
                        metadata=meta,
                    )
                )

        if len(selected) >= count:
            return selected

        # Fallback to deterministic ranking if LLM output was partial
        return self.select_complementary_seeds(topic=topic, direction=direction, count=count)

    def select_complementary_seeds(
        self,
        topic: str,
        direction: str = "",
        target_archetype: ArticleArchetype | None = None,
        count: int = 3,
    ) -> list[SeedRoleAssignment]:
        """
        Stage 2 (Deterministic Fallback): Role-based complementary seed selection.
        - Fixed ranking bug: relevance is positively weighted (10x), not inverted.
        - Episode/asset features serve as secondary tie-breakers, not overpowering relevance.
        """
        candidates = self.search_candidates(topic=topic, direction=direction, top_k=20)
        if not candidates:
            return []

        selected: list[SeedRoleAssignment] = []
        selected_ids: set[str] = set()
        recent_seed_ids = self.repo.get_recently_used_seed_ids(days=7)

        # -------------------------------------------------------------
        # 1. Select Seed #1: Domain & Case Seed
        # -------------------------------------------------------------
        def score_seed1(cand):
            art, meta, rank = cand
            # rank is positive normalized hybrid score (0.0 ~ 1.0)
            relevance = rank * 10.0
            episode_bonus = min(len(meta.notable_episodes) * 0.2, 0.6)
            has_metrics = 0.3 if ReusableAssetType.QUANTITATIVE_METRICS in meta.reusable_asset_types else 0.0
            cooldown_penalty = -2.0 if art.doc_id in recent_seed_ids else 0.0
            return relevance + episode_bonus + has_metrics + cooldown_penalty

        sorted_seed1 = sorted(candidates, key=score_seed1, reverse=True)
        seed1_art, seed1_meta, _ = sorted_seed1[0]
        selected.append(
            SeedRoleAssignment(
                seed_type="domain_case",
                doc_id=seed1_art.doc_id,
                title=seed1_art.title,
                reason=f"주제({topic})와의 높은 연관성 및 생생한 현장 사례/에피소드({len(seed1_meta.notable_episodes)}건) 제공",
                metadata=seed1_meta,
            )
        )
        selected_ids.add(seed1_art.doc_id)

        if count == 1 or len(candidates) == 1:
            return selected

        # -------------------------------------------------------------
        # 2. Select Seed #2: Perspective & Framework Seed
        # -------------------------------------------------------------
        dir_keywords = self.extract_keywords(direction) if direction else []

        def score_seed2(cand):
            art, meta, rank = cand
            if art.doc_id in selected_ids:
                return -999.0

            relevance = rank * 8.0
            jaccard = self.jaccard_similarity(seed1_meta.topic_tags, meta.topic_tags)
            diversity_score = (1.0 - jaccard) * 1.0

            dir_matches = sum(
                1 for kw in dir_keywords if kw in meta.reframing_logic or any(kw in step for step in meta.solution_framework)
            )
            framework_strength = min(len(meta.solution_framework) * 0.2, 0.6)
            cooldown_penalty = -2.0 if art.doc_id in recent_seed_ids else 0.0

            return relevance + diversity_score + (dir_matches * 1.0) + framework_strength + cooldown_penalty

        sorted_seed2 = sorted(candidates, key=score_seed2, reverse=True)
        seed2_cand = sorted_seed2[0]
        if seed2_cand[0].doc_id not in selected_ids:
            seed2_art, seed2_meta, _ = seed2_cand
            selected.append(
                SeedRoleAssignment(
                    seed_type="perspective_framework",
                    doc_id=seed2_art.doc_id,
                    title=seed2_art.title,
                    reason=f"통념을 뒤집는 관점 전환('{seed2_meta.reframing_logic[:30]}...') 및 단계별 실행 프레임워크 제공",
                    metadata=seed2_meta,
                )
            )
            selected_ids.add(seed2_art.doc_id)

        if count == 2 or len(selected) >= count or len(candidates) <= len(selected):
            return selected

        # -------------------------------------------------------------
        # 3. Select Seed #3: Structure & Asset Seed
        # -------------------------------------------------------------
        def score_seed3(cand):
            art, meta, rank = cand
            if art.doc_id in selected_ids:
                return -999.0

            relevance = rank * 6.0
            arch_match = 1.0 if target_archetype and meta.article_archetype == target_archetype else 0.0
            practical_assets = {
                ReusableAssetType.PROMPT_TEMPLATE,
                ReusableAssetType.CHECKLIST_TABLE,
                ReusableAssetType.BEFORE_AFTER_COMPARISON,
                ReusableAssetType.STEP_DIAGRAM,
            }
            asset_matches = min(sum(1 for a in meta.reusable_asset_types if a in practical_assets) * 0.3, 0.9)
            has_image = 0.2 if art.image_count > 0 else 0.0
            cooldown_penalty = -2.0 if art.doc_id in recent_seed_ids else 0.0

            return relevance + arch_match + asset_matches + has_image + cooldown_penalty

        sorted_seed3 = sorted(candidates, key=score_seed3, reverse=True)
        seed3_cand = sorted_seed3[0]
        if seed3_cand[0].doc_id not in selected_ids:
            seed3_art, seed3_meta, _ = seed3_cand
            selected.append(
                SeedRoleAssignment(
                    seed_type="structure_asset",
                    doc_id=seed3_art.doc_id,
                    title=seed3_art.title,
                    reason=f"글의 서사 구조({seed3_meta.article_archetype.value}) 및 실무 도구(체크리스트/프롬프트/시각자료) 보완",
                    metadata=seed3_meta,
                )
            )
            selected_ids.add(seed3_art.doc_id)

        return selected
