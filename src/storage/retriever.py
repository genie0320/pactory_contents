"""Cross-seed retrieval and role-based complementary ranking engine."""

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
    "아니다", "그냥", "단지", "약간", "조금", "항상", "자주", "가끔"
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
        particles = ("은", "는", "이", "가", "을", "를", "의", "에", "에서", "으로", "로", "와", "과", "하고", "도", "에게", "보다")
        endings = ("해요", "어요", "다고", "으면", "어서", "지만", "었다", "했다", "한다", "된다", "이다", "이며")
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
                norm_bm25 = 1.0 / (1.0 + abs(raw_rank)) if raw_rank != 0.0 else 0.1
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
            # Fallback ranking if vector ranking fails
            if recent_seed_ids:
                candidates.sort(
                    key=lambda x: (x[2] * (0.75 if x[0].doc_id in recent_seed_ids else 1.0)),
                    reverse=False,
                )
            return candidates[:top_k]

    def retrieve_seeds(
        self,
        topic: str,
        user_direction: str = "",
        target_archetype: ArticleArchetype | None = None,
        count: int = 3,
    ) -> list[SeedRoleAssignment]:
        """Convenience alias for select_complementary_seeds."""
        return self.select_complementary_seeds(
            topic=topic,
            direction=user_direction,
            target_archetype=target_archetype,
            count=count,
        )

    def select_complementary_seeds(
        self,
        topic: str,
        direction: str = "",
        target_archetype: ArticleArchetype | None = None,
        count: int = 3,
    ) -> list[SeedRoleAssignment]:
        """
        Stage 2: Role-based complementary seed selection.
        - Seed #1 (Domain & Case Seed): highest topic BM25 relevance & rich notable episodes.
        - Seed #2 (Perspective & Framework Seed): lower overlap with Seed 1, aligns with direction.
        - Seed #3 (Structure & Asset Seed): matches archetype or possesses practical reusable assets.
        """
        candidates = self.search_candidates(topic=topic, direction=direction, top_k=15)
        if not candidates:
            return []

        selected: list[SeedRoleAssignment] = []
        selected_ids: set[str] = set()
        recent_seed_ids = self.repo.get_recently_used_seed_ids(days=7)

        is_self_mgmt_relevant = any(
            w in (topic + " " + direction)
            for w in [
                "미루", "의지", "습관", "자기관리", "자책", "완벽주의",
                "게으름", "마찰", "루틴", "멘탈", "마인드셋", "동기부여",
            ]
        )

        # -------------------------------------------------------------
        # 1. Select Seed #1: Domain & Case Seed
        # -------------------------------------------------------------
        def score_seed1(cand):
            art, meta, rank = cand
            episode_bonus = len(meta.notable_episodes) * 0.5
            has_metrics = 1.0 if ReusableAssetType.QUANTITATIVE_METRICS in meta.reusable_asset_types else 0.0
            penalty = -25.0 if (not is_self_mgmt_relevant and meta.primary_category == "자기관리") else 0.0
            cooldown_penalty = -5.0 if art.doc_id in recent_seed_ids else 0.0
            # FTS5 bm25 rank is negative or lower is better; here invert for sorting
            return (-rank) + episode_bonus + has_metrics + penalty + cooldown_penalty

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

            # Diversity factor: penalize high jaccard overlap with Seed 1 tags
            jaccard = self.jaccard_similarity(seed1_meta.topic_tags, meta.topic_tags)
            diversity_score = 1.0 - jaccard

            # Category / Archetype difference bonus
            arch_bonus = 0.5 if meta.article_archetype != seed1_meta.article_archetype else 0.0
            cat_bonus = 0.5 if meta.primary_category != seed1_meta.primary_category else 0.0

            # Direction relevance bonus
            dir_matches = sum(
                1 for kw in dir_keywords if kw in meta.reframing_logic or any(kw in step for step in meta.solution_framework)
            )
            framework_strength = len(meta.solution_framework) * 0.3
            penalty = -25.0 if (not is_self_mgmt_relevant and meta.primary_category == "자기관리") else 0.0
            cooldown_penalty = -5.0 if art.doc_id in recent_seed_ids else 0.0
            relevance = max(0.0, -rank) * 0.3

            return relevance + (diversity_score * 2.0) + arch_bonus + cat_bonus + (dir_matches * 1.5) + framework_strength + penalty + cooldown_penalty

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
            art, meta, _ = cand
            if art.doc_id in selected_ids:
                return -999.0

            penalty = -25.0 if (not is_self_mgmt_relevant and meta.primary_category == "자기관리") else 0.0
            arch_match = 2.0 if target_archetype and meta.article_archetype == target_archetype else 0.0
            practical_assets = {
                ReusableAssetType.PROMPT_TEMPLATE,
                ReusableAssetType.CHECKLIST_TABLE,
                ReusableAssetType.BEFORE_AFTER_COMPARISON,
                ReusableAssetType.STEP_DIAGRAM,
            }
            asset_matches = sum(1 for a in meta.reusable_asset_types if a in practical_assets)
            has_image = 1.0 if art.image_count > 0 else 0.0
            cooldown_penalty = -5.0 if art.doc_id in recent_seed_ids else 0.0

            return arch_match + (asset_matches * 1.0) + has_image + penalty + cooldown_penalty

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
