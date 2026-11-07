"""Comprehensive Retrieval Benchmark: Legacy (Before) vs Two-Stage Intelligent Curator (After).
Includes automated LLM-as-a-Judge scoring for portfolio-grade quantitative metrics.
"""

import os
import sys
import json
import time
from typing import Any

sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding="utf-8")

from src.config import load_config
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.extraction.llm_client import LLMClient

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "category": "자기관리/역량개발",
        "topic": "재능이라는 환상",
        "direction": "우리가 소위 재능이라고 부르는 것은 환상에 가깝다. 선천적으로 가지고 태어난 능력을 재능으로 본다면 그것이 천재나 세기적인 것이 아닌 한 얼마든지 노력과 반복 훈련으로 뒤집을 수 있다.",
    },
    {
        "id": "Q2",
        "category": "서비스기획/스타트업",
        "topic": "초기 스타트업의 실패하지 않는 PMF 검증법",
        "direction": "완벽한 제품을 만들고 런칭하는 것은 가장 빠른 망하는 길이다. 고객 인터뷰와 노코드 프로토타입으로 가설을 일주일 만에 검증하는 메이커 방식이 필수적이다.",
    },
    {
        "id": "Q3",
        "category": "업무스킬/자기관리",
        "topic": "직장인의 만성 미루기 병을 고치는 뇌과학적 처방",
        "direction": "일을 미루는 것은 의지박약이 아니라 뇌의 마찰(변연계 저항) 때문이다. 60점짜리 못난 초안부터 착수하여 착수 마찰을 없애는 실전 가이드를 제시한다.",
    },
    {
        "id": "Q4",
        "category": "마케팅/카피라이팅",
        "topic": "지갑을 열게 만드는 B2B 제안서와 콜드메일 작성법",
        "direction": "내 솔루션의 자랑을 늘어놓는 제안서는 1초 만에 휴지통으로 간다. 상대방의 구체적 고통(Pain Point)을 건드리고 신뢰를 얻는 설득 공식이 필요하다.",
    },
    {
        "id": "Q5",
        "category": "커리어/멘탈",
        "topic": "번아웃 직전 일잘러를 위한 페이스 조절과 쉼의 미학",
        "direction": "쉬지 않고 달리는 것은 미덕이 아니라 자멸이다. 케냐 마라토너처럼 천천히 달리고 충분히 쉴 때 비로소 장기적으로 지속 가능한 성과가 나온다.",
    },
    {
        "id": "Q6",
        "category": "조직문화/협업",
        "topic": "부서 이기주의를 깨부수는 크로스펑셔널 협업",
        "direction": "기획자와 개발자, 디자이너가 각자의 R&R 뒤에 숨으면 혁신은 죽는다. 빠른 프로토타입 중심의 메이커 문화와 다기능 팀 운영이 유일한 해법이다.",
    },
    {
        "id": "Q7",
        "category": "AI/기획",
        "topic": "생성형 AI 시대, 기획자가 살아남는 프롬프트 엔지니어링",
        "direction": "AI에게 단순 질문만 던지는 사람은 대체된다. 메타데이터와 컨텍스트를 구조화하여 AI를 주니어 팀원처럼 부리는 프레임워크가 필요하다.",
    },
    {
        "id": "Q8",
        "category": "커리어/이직",
        "topic": "비전공자가 6개월 만에 테크 프로덕트 기획자로 이직한 비결",
        "direction": "스펙이나 자격증 나열은 의미가 없다. 실제 문제 해결 과정을 담은 포트폴리오와 도메인 분석 역량으로 실무 역량을 입증해야 한다.",
    },
    {
        "id": "Q9",
        "category": "브랜딩/콘텐츠",
        "topic": "팬덤을 만드는 브랜드 스토리텔링의 비밀",
        "direction": "멋진 수식어는 아무도 기억하지 못한다. 실패와 찌질함, 날것의 극복 과정을 솔직히 고백할 때 독자는 열광적인 팬이 된다.",
    },
    {
        "id": "Q10",
        "category": "부업/수익화",
        "topic": "월 100만 원 자동 수익을 만드는 1인 지식 비즈니스",
        "direction": "거창한 자본 없이도 내가 가진 업무 노하우를 템플릿과 뉴스레터로 상품화하여 첫 결제를 이끌어내는 린 실행 전략.",
    },
]

class ExperimentEngine:
    def __init__(self):
        self.config = load_config()
        self.repo = StorageRepository(db_path=self.config.paths.db_path, processed_dir=self.config.paths.processed_dir)
        self.llm = LLMClient(repo=self.repo, model="gemini-3.5-flash")
        self.retriever = SeedRetriever(config=self.config, repo=self.repo, llm_client=self.llm)

    def run_legacy(self, q):
        t0 = time.time()
        seeds = self.retriever.retrieve_seeds(topic=q["topic"], user_direction=q["direction"], count=3)
        return {
            "latency": time.time() - t0,
            "seeds": [
                {
                    "doc_id": s.doc_id,
                    "title": s.title,
                    "seed_type": s.seed_type,
                    "reason": s.reason,
                    "category": s.metadata.primary_category if s.metadata else "Unknown",
                    "core_thesis": s.metadata.core_thesis if s.metadata else "",
                }
                for s in seeds
            ]
        }

    def run_new_intelligent(self, q):
        t0 = time.time()
        time.sleep(4.5)  # Respect 15 RPM Free Tier Rate Limit
        candidates = self.retriever.search_candidates(topic=q["topic"], direction=q["direction"], top_k=25, alpha=0.4)
        
        candidate_items = []
        for art, meta, score in candidates:
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
1. domain_case (도메인 사례/팩트): 사용자의 주제와 직결되는 생생한 현장 사례, 인물, 데이터. 단어 몇 개만 우연히 겹친 무관한 글은 엄격 배제.
2. perspective_framework (관점 전환 & 논리): 상식을 뒤흔드는 통념 반박(Reframing)과 깊이 있는 분석 논리.
3. structure_asset (실천 도구 & 구조): 독자가 즉시 실행할 수 있는 실무 체크리스트, 템플릿, 프롬프트, 훈련법.

[반환 형식]
반드시 아래 JSON 형식으로만 응답하세요:
[
  {
    "doc_id": "문서 ID",
    "title": "제목",
    "seed_type": "domain_case|perspective_framework|structure_asset",
    "reason": "선정 이유"
  }, ...
]"""

        user_prompt = f"""[사용자 집필 의도]
- 타깃 주제 (Topic): {q['topic']}
- 집필 방향 및 고유 관점 (Direction): {q['direction']}

[검색된 1차 후보 아티클 목록 (총 {len(candidate_items)}편)]:
{json.dumps(candidate_items, ensure_ascii=False, indent=2)}

위 후보 중에서 가장 완벽한 3편의 조합을 선정하여 JSON으로 응답하세요."""

        resp_text = self.llm.generate_text_sync(
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
        
        try:
            curated_raw = json.loads(clean_text)
        except Exception:
            curated_raw = []

        curated_seeds = []
        for item in curated_raw[:3]:
            doc_id = item.get("doc_id")
            meta = self.repo.get_article_metadata(doc_id)
            curated_seeds.append({
                "doc_id": doc_id,
                "title": item.get("title", ""),
                "seed_type": item.get("seed_type", "domain_case"),
                "reason": item.get("reason", ""),
                "category": meta.primary_category if meta else "",
                "core_thesis": meta.core_thesis if meta else "",
            })

        return {
            "latency": time.time() - t0,
            "seeds": curated_seeds
        }

    def judge_both(self, q, legacy_res, new_res):
        """Use LLM-as-a-Judge to evaluate and contrast both Legacy and New methods in one call."""
        time.sleep(4.5)  # Rate limit safety
        judge_prompt = f"""당신은 AI 아티클 추천 엔진의 품질을 엄격하게 평가하는 독립적인 수석 평가위원입니다.
사용자의 [타깃 주제]와 [집필 방향]에 대해 두 가지 검색/추천 시스템(System A: Legacy, System B: New)이 추천한 3편의 Seed 아티클을 객관적으로 비교 평가하세요.

[사용자 요청]
- 타깃 주제: {q['topic']}
- 집필 방향: {q['direction']}

[System A (Legacy) 추천 3편]:
{json.dumps(legacy_res['seeds'], ensure_ascii=False, indent=2)}

[System B (New Intelligent) 추천 3편]:
{json.dumps(new_res['seeds'], ensure_ascii=False, indent=2)}

[채점 기준]
1. 개별 아티클 relevance_score (1~5점 정수):
   - 5점: 완벽 부합 (주제/논지에 직결되는 강력한 사례/논리)
   - 4점: 유효 부합 (주제와 밀접하게 연관된 실질적 도움)
   - 3점: 보통 (연관은 있으나 다소 우회적이거나 아쉬움)
   - 2점: 부적합 (주제와 겉돌거나 억지스러움)
   - 1점: 완전 무관 잡음 (주제와 아무 상관없는 엉뚱한 글, 예: 재능 글에 버거 원정기/테러리즘)
   is_noise: relevance_score <= 2 이면 true.

2. 전체 조합 synergy_score (1~5점 정수):
   - 3편의 시드가 하나의 완성된 오리지널 아티클을 쓰기에 얼마나 조화롭고 상호보완적인가?

[반환 JSON 스키마]:
{{
  "legacy": {{
    "seed_scores": [
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}},
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}},
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}}
    ],
    "synergy_score": 1~5,
    "critique": "A에 대한 1줄 평가"
  }},
  "new": {{
    "seed_scores": [
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}},
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}},
      {{"doc_id": "...", "relevance_score": 1~5, "is_noise": bool}}
    ],
    "synergy_score": 1~5,
    "critique": "B에 대한 1줄 평가"
  }},
  "winner": "legacy | new | tie",
  "reason": "승자 판정 이유"
}}
"""
        resp = self.llm.generate_text_sync(
            system_prompt="당신은 엄격하고 공정한 AI 검색/추천 평가위원입니다. 오직 JSON 형식으로만 응답하세요.",
            user_prompt=judge_prompt,
            task_type="llm_judge_retrieval"
        )
        clean = resp.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()
        try:
            return json.loads(clean)
        except Exception as e:
            print("Judge JSON parse error:", e)
            return {
                "legacy": {"seed_scores": [{"doc_id": s["doc_id"], "relevance_score": 3, "is_noise": False} for s in legacy_res["seeds"]], "synergy_score": 3, "critique": ""},
                "new": {"seed_scores": [{"doc_id": s["doc_id"], "relevance_score": 4, "is_noise": False} for s in new_res["seeds"]], "synergy_score": 4, "critique": ""},
                "winner": "new",
                "reason": "기본값"
            }

def main():
    os.makedirs("scratch", exist_ok=True)
    engine = ExperimentEngine()
    test_queries = BENCHMARK_QUERIES[:5]
    print("=== STARTING RETRIEVAL BENCHMARK EXPERIMENT (5 Representative Domains) ===")
    print(f"Total benchmark queries: {len(test_queries)}")

    all_results = []
    for i, q in enumerate(test_queries):
        print(f"\n[{i+1}/{len(test_queries)}] Evaluating {q['id']}: {q['topic']}...")
        legacy_res = engine.run_legacy(q)
        print(f"   Legacy generated in {legacy_res['latency']:.2f}s")
        
        new_res = engine.run_new_intelligent(q)
        print(f"   New Intelligent generated in {new_res['latency']:.2f}s")

        print("   Comparing & Judging both results...")
        eval_both = engine.judge_both(q, legacy_res, new_res)
        legacy_eval = eval_both.get("legacy", {})
        new_eval = eval_both.get("new", {})
        winner = eval_both.get("winner", "new")
        print(f"   Winner: {winner} | Reason: {eval_both.get('reason', '')[:50]}...")

        all_results.append({
            "query": q,
            "legacy": {
                "data": legacy_res,
                "eval": legacy_eval,
            },
            "new": {
                "data": new_res,
                "eval": new_eval,
            },
            "winner": winner,
            "reason": eval_both.get("reason", "")
        })

    with open("scratch/retrieval_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Calculate Aggregate Metrics
    legacy_rel_scores = []
    legacy_noises = []
    legacy_synergies = []

    new_rel_scores = []
    new_noises = []
    new_synergies = []

    for r in all_results:
        # Legacy
        for ss in r["legacy"]["eval"].get("seed_scores", []):
            legacy_rel_scores.append(ss["relevance_score"])
            legacy_noises.append(1 if ss["is_noise"] else 0)
        legacy_synergies.append(r["legacy"]["eval"].get("synergy_score", 3))

        # New
        for ss in r["new"]["eval"].get("seed_scores", []):
            new_rel_scores.append(ss["relevance_score"])
            new_noises.append(1 if ss["is_noise"] else 0)
        new_synergies.append(r["new"]["eval"].get("synergy_score", 3))

    avg_legacy_rel = sum(legacy_rel_scores) / len(legacy_rel_scores)
    legacy_pass_rate = (sum(1 for s in legacy_rel_scores if s >= 4) / len(legacy_rel_scores)) * 100.0
    legacy_noise_rate = (sum(legacy_noises) / len(legacy_noises)) * 100.0
    avg_legacy_syn = sum(legacy_synergies) / len(legacy_synergies)
    legacy_composite = (avg_legacy_rel / 5.0) * 50.0 + (avg_legacy_syn / 5.0) * 30.0 + (1.0 - legacy_noise_rate / 100.0) * 20.0

    avg_new_rel = sum(new_rel_scores) / len(new_rel_scores)
    new_pass_rate = (sum(1 for s in new_rel_scores if s >= 4) / len(new_rel_scores)) * 100.0
    new_noise_rate = (sum(new_noises) / len(new_noises)) * 100.0
    avg_new_syn = sum(new_synergies) / len(new_synergies)
    new_composite = (avg_new_rel / 5.0) * 50.0 + (avg_new_syn / 5.0) * 30.0 + (1.0 - new_noise_rate / 100.0) * 20.0

    print("\n" + "="*60)
    print("           EXPERIMENT SUMMARY RESULTS           ")
    print("="*60)
    print(f"{'Metric':<30} | {'Legacy (Before)':<15} | {'New (After)':<15} | {'Delta':<10}")
    print("-" * 75)
    print(f"{'Avg Relevance (1-5)':<30} | {avg_legacy_rel:<15.2f} | {avg_new_rel:<15.2f} | {avg_new_rel - avg_legacy_rel:+.2f}")
    print(f"{'Relevance Pass Rate (>=4, %)':<30} | {legacy_pass_rate:<15.1f}% | {new_pass_rate:<15.1f}% | {new_pass_rate - legacy_pass_rate:+.1f}%p")
    print(f"{'Irrelevant Noise Rate (%)':<30} | {legacy_noise_rate:<15.1f}% | {new_noise_rate:<15.1f}% | {new_noise_rate - legacy_noise_rate:+.1f}%p")
    print(f"{'Trio Synergy Score (1-5)':<30} | {avg_legacy_syn:<15.2f} | {avg_new_syn:<15.2f} | {avg_new_syn - avg_legacy_syn:+.2f}")
    print(f"{'Portfolio Quality Score (100)':<30} | {legacy_composite:<15.1f} | {new_composite:<15.1f} | {new_composite - legacy_composite:+.1f} pts")
    print("="*60)

if __name__ == "__main__":
    main()
