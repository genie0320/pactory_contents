"""Cross-seed retrieval and role-based complementary ranking engine."""

import re
from typing import Dict, List, Optional, Set, Tuple
import sqlite3

from src.config import AppConfig, load_config
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
KOREAN_STOPWORDS: Set[str] = {
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

# Domain synonym expansion to bridge terminology discrepancies (e.g. 컨셉 vs 콘셉트)
DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    "컨셉": ["컨셉", "콘셉트", "카피", "브랜딩", "브랜드", "기획", "아이디어"],
    "콘셉트": ["콘셉트", "컨셉", "카피", "브랜딩", "브랜드", "기획"],
    "카피": ["카피", "카피라이팅", "컨셉", "브랜딩", "슬로건"],
    "브랜드": ["브랜드", "브랜딩", "리브랜딩", "팬덤", "부계정"],
    "보고": ["보고", "보고서", "보고법", "기획서", "회사어", "두괄식"],
    "보고서": ["보고서", "보고", "기획서", "자료조사"],
    "미루기": ["미루기", "미루는", "의지박약", "완벽주의", "착수"],
    "노션": ["노션", "업무관리", "생산성", "대시보드", "템플릿"],
    "팀장": ["팀장", "리더십", "중간관리자", "위임"],
    "템플릿": ["템플릿", "자동화", "반복업무", "효율"],
}


class SeedRetriever:
    """Retrieves and ranks complementary Seed articles based on FTS5 BM25 and role diversity."""

    def __init__(self, config: Optional[AppConfig] = None, repo: Optional[StorageRepository] = None):
        self.config = config or load_config()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.db_path = self.config.paths.db_path

    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract meaningful keywords stripping Korean particles, predicate endings, and punctuation."""
        cleaned = re.sub(r"[^\w\s가-힣a-zA-Z0-9]", " ", text)
        tokens = cleaned.split()
        particles = ("은", "는", "이", "가", "을", "를", "의", "에", "에서", "으로", "로", "와", "과", "하고", "도", "에게", "보다")
        endings = ("해요", "어요", "다고", "으면", "어서", "지만", "었다", "했다", "한다", "된다", "이다", "이며")
        keywords: List[str] = []
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
                if t_clean in DOMAIN_SYNONYMS:
                    keywords.extend(DOMAIN_SYNONYMS[t_clean])
        return list(dict.fromkeys(keywords))

    @staticmethod
    def jaccard_similarity(tags1: List[str], tags2: List[str]) -> float:
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
    ) -> List[Tuple[ArticleRecord, ArticleMetadata, float]]:
        """
        Stage 1: FTS5 BM25 retrieval with multi-column weighting + LIKE fallback.
        Topic keywords are amplified 3x to ensure core intent dictates ranking.
        """
        topic_keywords = self.extract_keywords(topic)
        direction_keywords = self.extract_keywords(direction) if direction else []
        all_keywords = (topic_keywords * 3) + direction_keywords

        if not all_keywords:
            all_keywords = [topic.strip()]

        # Construct FTS5 match query: 'keyword1 OR keyword2 ...'
        fts_query = " OR ".join(f'"{kw}"' for kw in all_keywords if kw)

        conn = get_connection(self.db_path)
        candidates: List[Tuple[ArticleRecord, ArticleMetadata, float]] = []
        seen_doc_ids: Set[str] = set()

        try:
            cursor = conn.cursor()
            # FTS5 columns: doc_id(UNINDEXED), title(2.0), primary_category(1.0),
            # target_audience(1.5), core_problem(2.5), reframing_logic(3.0),
            # core_thesis(2.0), solution_framework(2.0), notable_episodes(1.5),
            # topic_tags(2.5), asset_captions(1.0)
            if fts_query:
                sql = """
                SELECT doc_id, bm25(metadata_fts, 2.0, 1.0, 1.5, 2.5, 3.0, 2.0, 2.0, 1.5, 2.5, 1.0) as rank
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
                params: List[Any] = []
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

        return candidates[:top_k]

    def select_complementary_seeds(
        self,
        topic: str,
        direction: str = "",
        target_archetype: Optional[ArticleArchetype] = None,
        count: int = 3,
    ) -> List[SeedRoleAssignment]:
        """
        Stage 2: Role-based complementary seed selection.
        - Seed #1 (Domain & Case Seed): highest topic BM25 relevance & rich notable episodes.
        - Seed #2 (Perspective & Framework Seed): lower overlap with Seed 1, aligns with direction.
        - Seed #3 (Structure & Asset Seed): matches archetype or possesses practical reusable assets.
        """
        candidates = self.search_candidates(topic=topic, direction=direction, top_k=15)
        if not candidates:
            return []

        selected: List[SeedRoleAssignment] = []
        selected_ids: Set[str] = set()

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
            # FTS5 bm25 rank is negative or lower is better; here invert for sorting
            return (-rank) + episode_bonus + has_metrics + penalty

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
            relevance = max(0.0, -rank) * 0.3

            return relevance + (diversity_score * 2.0) + arch_bonus + cat_bonus + (dir_matches * 1.5) + framework_strength + penalty

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

            return arch_match + (asset_matches * 1.0) + has_image + penalty

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
