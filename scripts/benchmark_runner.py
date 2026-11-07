"""Benchmark runner comparing Legacy (Before) vs New (After) Seed Retrieval."""

import os
import sys
import json
import time
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding="utf-8")

from src.config import load_config
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.extraction.llm_client import LLMClient

# 10 Benchmark Queries
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

def run_legacy_benchmark():
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    retriever = SeedRetriever(config=config, repo=repo)

    results = []
    start_all = time.time()
    for q in BENCHMARK_QUERIES:
        t0 = time.time()
        seeds = retriever.retrieve_seeds(topic=q["topic"], user_direction=q["direction"], count=3)
        latency = time.time() - t0
        results.append({
            "id": q["id"],
            "topic": q["topic"],
            "direction": q["direction"],
            "latency": latency,
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
        })
    print(f"Legacy benchmark finished in {time.time() - start_all:.2f}s")
    with open("scratch/legacy_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    res = run_legacy_benchmark()
    for r in res:
        print(f"[{r['id']}] {r['topic']}")
        for s in r["seeds"]:
            print(f"   - ({s['seed_type']}) [{s['doc_id']}] {s['title']} ({s['category']})")
