# [SDD] 경량 메타데이터 인덱스 및 아티클 교차 합성 파이프라인 (Lightweight Seed Synthesis Engine)

* **문서 버전**: v2.0 (Antigravity 구현 명세서 — 원문 탈동조화 합성, 웹 UI 워크스페이스, 사용자 스타일 학습 루프 포함)
* **기반 문서**: `PRD.txt` (아티클 메타데이터 인덱싱 및 교차 합성 파이프라인)
* **런타임 환경**: Python 3.11+ / 로컬 파일시스템 및 SQLite3 (FTS5) / Streamlit 로컬 웹 스튜디오

## 1. 시스템 설계 개요 및 핵심 아키텍처 원칙

본 문서는 로컬 폴더에 투입되는 약 4,000편 이상의 다양한 아티클(PDF, Markdown, TXT)을 전처리하여 **원문 텍스트, 시각 에셋(이미지/도표), 정형 메타데이터 인덱스로 분리 저장**하고, 사용자가 원하는 **주제(Topic)와 집필 방향(Direction/Angle)**을 입력했을 때 상호 보완적인 **Seed 아티클 2~3편을 교차 매칭하여 새로운 초안(Draft)을 합성**하며, **웹 UI에서 Seed 이미지 조회·초안 편집·‘나의 결과물’ 저장 및 문체 학습**까지 수행하는 통합 파이프라인의 소프트웨어 상세 설계서(SDD)입니다.

### 1.1 핵심 설계 원칙 (Architectural Principles)

1. **Zero-Vector, Zero-Chunking 원칙**:
   * 무거운 벡터 DB 데몬이나 로컬 임베딩 모델을 일절 사용하지 않으며, 문서를 조각내지(Chunking) 않고 **단일 완결 문서 단위**로 맥락을 보존합니다.
2. **3-Tier 분리 저장소 + ‘나의 결과물(My Corpus)’ 분리 아키텍처**:
   * SQLite DB 파일 비대화를 막고 데이터 재활용성을 높이기 위해 **① 원본 보관소(`archive/`)**, **② 정제 본문 및 추출 이미지 저장소(`processed/`)**, **③ 초경량 메타데이터 검색 인덱스(`index/catalog.db`)**, **④ 사용자가 직접 퇴고해 확정한 결과물 및 문체 자산(`my_corpus/`)**을 물리적으로 분리합니다.
3. **PDF 멀티모달 전처리 (Text + Visual Asset Extraction)**:
   * PDF 아티클의 경우 단순 텍스트 추출을 넘어 상·하단 반복 보일러플레이트(뉴스레터 배너, 저작권 문구 등)를 제거하고, 본문 내 핵심 도표·스크린샷 이미지를 추출하여 페이지 및 주변 캡션(`║ ... ©저자`)과 함께 매핑합니다.
4. **원문 탈동조화(De-contextualized Distillation) 및 사후 스타일 결합(Late-Binding Style)**:
   * 초안이 Seed 원문의 문장·어투·특유 포맷을 그대로 베끼는 현상(Anchoring Bias)을 막기 위해, **초안 작성 LLM에는 Seed 원문(Raw Text)을 직접 노출하지 않고 개조식 ‘순수 팩트·논리 시트(Distilled Material Sheet)’만 전달**합니다.
   * 글의 스타일(문체/포맷)은 파이프라인 초기 단계에서 인위적으로 강제하지 않으며, 사용자가 웹 UI에서 초안을 직접 수정하여 저장한 **‘나의 결과물’이 5편 이상 누적되었을 때 Diff(수정 전후 비교) 기반으로 나만의 스타일 프로필을 추출해 마지막 윤문 단계에 적용**합니다.

## 2. 디렉터리 구조 및 분리 저장소 설계

Antigravity가 생성해야 할 프로젝트 루트 및 데이터 저장소 레이아웃은 다음과 같습니다.

```text
seed-synthesis-engine/
├── pyproject.toml                 # 의존성 및 패키지 메타데이터 정의
├── .env.example                   # LLM API 키 및 기본 경로 환경변수 템플릿
├── config.yaml                    # 파이프라인 하이퍼파라미터 및 통제 어휘(Taxonomy) 설정
├── run.py                         # CLI 엔트리포인트 (ingest, extract, search, generate, ui)
├── src/
│   ├── __init__.py
│   ├── config.py                  # 환경변수 및 YAML 설정 로더
│   ├── models.py                  # Pydantic v2 스키마 (메타데이터, 재료 시트, 블루프린트, 스타일 프로필)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── scanner.py             # 인박스 폴더 감시, 해시(SHA-256) 중복 검사, 파일 라우팅
│   │   ├── pdf_processor.py       # PDF 텍스트 정제, 보일러플레이트 제거, 이미지/캡션 분리 추출
│   │   └── text_normalizer.py     # MD/TXT 인코딩 정규화 및 섹션 헤더 구조화
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── llm_client.py          # 비동기 LLM 래퍼 (OpenAI/Anthropic/Gemini Structured Outputs)
│   │   ├── prompts.py             # 추출, 재료 탈색(Distillation), 합성, 스타일 학습용 프롬프트
│   │   └── batch_extractor.py     # Semaphore 동시성 제어, 지수 백오프, 체크포인트 및 작업 상태 기록
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                  # SQLite 커넥션, DDL 초기화 (작업 로그 및 사용자 결과물 테이블 포함)
│   │   ├── repository.py          # 메타데이터/에셋/작업상태/내 결과물 CRUD 및 파일시스템 연동
│   │   └── retriever.py           # FTS5 BM25 검색 + 역할별 Seed 다양성 리랭킹 엔진
│   ├── synthesis/
│   │   ├── __init__.py
│   │   ├── distiller.py           # [핵심] Seed 원문에서 문체/포맷을 벗겨낸 '개조식 재료 시트' 추출
│   │   ├── planner.py             # 선별된 Seed 메타데이터 기반 '초안 설계도(Blueprint)' 생성
│   │   ├── synthesizer.py         # 원문 배제 + 재료 시트 기반 중립 초안 생성 (선택적 스타일 프로필 적용)
│   │   └── style_learner.py       # 'AI 초안 vs 내 최종본' 5개 이상 누적 시 Diff 분석으로 스타일 프로필 생성
│   └── ui/
│       ├── __init__.py
│       ├── app.py                 # Streamlit 기반 통합 로컬 웹 워크스페이스 메인 엔트리
│       └── views/
│           ├── dashboard_view.py  # [Tab 1] 작업 모니터링(진행률/로그) 및 Seed 인덱스 탐색기
│           ├── generator_view.py  # [Tab 2] 주제/방향 입력, Seed 매칭 확인, 초안 생성 실행
│           ├── studio_view.py     # [Tab 3] 초안 편집기 + Seed 원본 이미지 갤러리 조회 + '나의 결과물' 저장
│           └── style_view.py      # [Tab 4] 저장된 '나의 결과물(5+)' 관리 및 나만의 스타일 프로필 추출/적용
├── data/                          # 런타임 데이터 디렉터리 (분리 저장)
│   ├── inbox/                     # [입력] 사용자가 새 아티클(PDF, MD, TXT)을 넣어두는 폴더
│   ├── archive/                   # [보관] 처리가 완료된 원본 파일 이동 보관
│   ├── processed/                 # [분리 저장] 정제된 원문 및 추출 데이터
│   │   ├── texts/                 # {doc_id}.md (정제된 마크다운 원문)
│   │   ├── metadata/              # {doc_id}.json (추출된 메타데이터 개별 JSON 백업)
│   │   └── assets/                # {doc_id}/img_p{page}_{idx}.png 및 manifest.json
│   ├── index/
│   │   └── catalog.db             # [인덱스] SQLite3 + FTS5 경량 인덱스 및 작업/초안 상태 DB
│   ├── drafts/                    # [초안] AI가 생성한 미확정 초안 마크다운 ({draft_id}.md)
│   └── my_corpus/                 # [나의 결과물] 사용자가 UI에서 직접 수정·확정한 최종본 및 스타일 자산
│       ├── articles/              # {creation_id}_final.md (내가 수정 완료한 최종 글)
│       ├── custom_assets/         # 참고 이미지를 보고 내가 새로 그려 넣은 이미지 보관
│       └── style_profile.json     # 5편 이상 누적 시 자동 추출된 '나만의 문체·구조 규칙'
└── tests/
    ├── test_ingestion.py
    ├── test_retriever.py
    ├── test_synthesizer.py
    └── test_style_learner.py
```

## 3. 초안의 'Seed 모방 현상' 해결을 위한 아키텍처 설계

### 3.1 문제 원인: 왜 초안이 Seed의 포맷과 문장을 그대로 따라 하는가?

기존 방식처럼 초안 작성 LLM 프롬프트에 **Seed 아티클 2~3편의 원문 전체(Full-text)**를 그대로 주입하면, LLM은 원문의 어휘, 문장 어미, 단락 호흡, 특유의 편집 포맷(예: 특정 플랫폼의 요약 박스, 질문형 소제목 패턴 등)에 강하게 **앵커링(Context Anchoring)**됩니다.

### 3.2 해결 전략: '단계별 역할 분리' (정보 추출과 스타일링의 완전 분리)

지금 단계는 Seed 데이터를 축적·정리하는 파이프라인이므로, 앞단에서 억지로 스타일을 지정하지 않고 **① 원문 문체 탈색(De-styling) → ② 중립 골격 합성(Neutral Draft) → ③ 인간 편집 피드백 기반 스타일 학습(Human-in-the-Loop Style Learning)**의 3단계로 분리합니다.

| 파이프라인 단계 | 기존 방식 (v1.0) | 개선된 방식 (v2.0 — 문체 탈동조화 & 사후 스타일 학습) | 기대 효과 |
| :--- | :--- | :--- | :--- |
| **1단계: Seed 재료 준비**<br>(`distiller.py`) | 선별된 Seed 2~3편의 **원문 전체(`.md`)**를 합성 프롬프트에 직접 투입 | 원문에서 수사적 표현·문체·고유 포맷을 완전히 제거하고, 오직 **[수치/팩트, 에피소드 인과관계, 프레임워크 단계, 표/프롬프트 데이터]**만 건조한 개조식(`DistilledMaterialSheet`)으로 추출 | LLM이 원문의 문장이나 포맷을 베끼려야 베낄 수 없는 물리적 차단벽 형성 |
| **2단계: 초안 합성**<br>(`synthesizer.py`) | 특정 요약 박스(`바쁘다면 이거라도!`) 등 원본 플랫폼 양식을 프롬프트에서 강제 | **Seed 원문을 보지 않은 상태**에서 `[합성 설계도(Blueprint) + 개조식 재료 시트]`만 가지고 주제와 방향에 맞춘 **담백한 표준 아티클 초안(Neutral Base Draft)** 작성 | Seed의 내용적 알맹이(사례·논리)만 흡수하고, 글의 전개와 문장은 새 주제에 맞게 독립적으로 생성 |
| **3단계: 스타일 완성**<br>(`studio_view.py` & `style_learner.py`) | 단발성 마크다운 파일 출력으로 종료 | 웹 UI에서 사용자가 Seed 이미지를 참고하며 초안을 직접 수정해 **‘나의 결과물’로 5편 이상 저장** → `[AI 초안 vs 내 최종본]`의 Diff를 분석해 **나만의 스타일 프로필(`style_profile.json`)**을 추출 후 이후 생성에 주입 | 초기에는 재료 정리에 집중하고, 내 결과물이 쌓인 뒤 자연스럽게 ‘내 문체와 포맷’을 자동화 |

## 4. 데이터 모델 및 스키마 상세 설계 (`src/models.py`, `src/storage/db.py`)

### 4.1 Pydantic v2 스키마 (`src/models.py`)

기존 `ArticleMetadata`와 `SynthesisBlueprint`에 더해, 원문 문체를 벗겨내는 **`DistilledMaterialSheet`**와 사용자 스타일 학습을 위한 **`UserStyleProfile`** 모델을 추가합니다.

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ArticleArchetype(str, Enum):
    TRIAL_AND_ERROR_RETRO = "trial_and_error_retro"       # 1인칭 시행착오 및 프로젝트 회고형
    STEP_BY_STEP_TUTORIAL = "step_by_step_tutorial"       # 실전 구축 및 단계별 튜토리얼형
    FRAMEWORK_CHECKLIST = "framework_checklist"           # 실무 프로세스 및 체크리스트 제안형
    CASE_STUDY_WORKSHOP = "case_study_workshop"           # 다중 사례 분석 및 실습 워크숍형
    BRAND_INTERVIEW_QA = "brand_interview_qa"             # 브랜드/창업가 스토리 강연 및 Q&A형
    TEMPLATE_CURATION = "template_curation"               # 로드맵 기반 템플릿/도구 모음집형

class ReusableAssetType(str, Enum):
    PROMPT_TEMPLATE = "prompt_template"
    CHECKLIST_TABLE = "checklist_table"
    BEFORE_AFTER_COMPARISON = "before_after_comparison"
    QUANTITATIVE_METRICS = "quantitative_metrics"
    FAILURE_EPISODE = "failure_episode"
    STEP_DIAGRAM = "step_diagram"

class VisualAssetItem(BaseModel):
    asset_id: str = Field(..., description="이미지 파일 식별자 (예: img_p04_01)")
    doc_id: str = Field(..., description="소속 Seed 문서 ID")
    page_no: int = Field(..., description="원본 PDF 페이지 번호")
    file_path: str = Field(..., description="processed/assets/ 내 상대 경로")
    caption: str = Field(default="", description="이미지 하단 또는 주변에서 추출된 캡션 텍스트")
    width: int
    height: int

class ArticleMetadata(BaseModel):
    target_audience: str = Field(..., description="타깃 독자 페르소나 및 처한 상황 (1~2문장)")
    core_problem: str = Field(..., description="독자가 겪고 있는 표면적 막막함 또는 핵심 질문 (1~2문장)")
    reframing_logic: str = Field(..., description="통념을 뒤집는 관점의 전환 공식 ('A가 아니라 B의 문제다')")
    core_thesis: str = Field(..., description="글 전체를 관통하는 핵심 결론 1문장")
    article_archetype: ArticleArchetype = Field(..., description="글의 전개 방식 및 장르 유형")
    hook_strategy: str = Field(..., description="도입부 독자 시선 유도 방식")
    solution_framework: List[str] = Field(..., min_length=2, max_length=6, description="단계별 해결 방법론 리스트")
    notable_episodes: List[str] = Field(..., min_length=1, max_length=4, description="구체적 사례, 시행착오, 실험 결과 요약")
    reusable_asset_types: List[ReusableAssetType] = Field(default_factory=list)
    primary_category: str = Field(..., description="대분류 도메인")
    topic_tags: List[str] = Field(..., min_length=3, max_length=7, description="핵심 키워드 태그")

class DistilledMaterialSheet(BaseModel):
    """[신규] 초안이 Seed의 문장과 포맷을 모방하지 않도록 원문에서 알맹이만 발췌한 건조한 개조식 재료 시트"""
    doc_id: str
    assigned_role: str = Field(..., description="이 Seed가 새 글에서 맡은 역할 (소재/사례 vs 관점/논리 vs 실무도구)")
    core_mechanism_bullets: List[str] = Field(
        ..., description="원문의 문체를 완전히 제거하고 인과관계와 작동 원리만 건조한 명사형/개조식으로 요약한 리스트"
    )
    extracted_facts_and_numbers: List[str] = Field(
        ..., description="인용 가능한 정량 수치, 소요 기간, 전후 변화 데이터, 실험 조건"
    )
    case_causal_chains: List[str] = Field(
        ..., description="[상황 → 문제 발생 → 개입/해결책 → 결과] 구조로만 축약한 에피소드 뼈대 (원문 어투 배제)"
    )
    raw_templates_or_criteria: List[str] = Field(
        default_factory=list, description="체크리스트 판단 기준, 프롬프트 핵심 조건 등 새 글의 도메인에 맞게 치환할 원재료"
    )

class SynthesisBlueprint(BaseModel):
    proposed_title: str = Field(..., description="새로 작성할 아티클의 가제")
    target_reader_definition: str = Field(..., description="새 글의 타깃 독자 및 핵심 페인포인트")
    synthesized_reframing: str = Field(..., description="Seed들의 관점을 결합하여 도출한 새 글만의 핵심 관점 전환 명제")
    role_assignments: List[str] = Field(..., description="각 Seed 문서(doc_id)에서 차용할 구체적 요소 명시")
    section_outline: List[str] = Field(..., description="새 글의 섹션별 소제목 및 핵심 내용 구성안 (4~6개 섹션)")
    visual_asset_recommendations: List[str] = Field(
        default_factory=list,
        description="선별된 Seed의 이미지(asset_id) 중 어느 섹션에 어떤 형태로 재구성/삽입하면 좋을지 제안"
    )

class UserStyleProfile(BaseModel):
    """[신규] 사용자가 직접 수정해 저장한 '나의 결과물' 5편 이상의 Diff에서 추출한 나만의 스타일 규칙"""
    profile_version: int = Field(default=1)
    based_on_creation_count: int = Field(..., description="분석에 사용된 내 결과물 개수 (최소 5개 권장)")
    preferred_tone_and_endings: List[str] = Field(..., description="선호하는 종결어미, 문장 길이, 호흡 규칙")
    structural_preferences: List[str] = Field(..., description="도입부 시작 방식, 소제목 네이밍 패턴, 단락 구성 특징")
    forbidden_patterns: List[str] = Field(..., description="사용자가 수정 과정에서 반복적으로 삭제·기피한 AI/Seed 특유 표현이나 포맷")
    signature_formatting_rules: List[str] = Field(..., description="사용자가 즐겨 쓰는 강조 방식, 리스트/표 배치 규칙")
```

### 4.2 SQLite3 데이터베이스 확장 스키마 (`src/storage/db.py`)

기존 4개 테이블(`articles`, `article_metadata`, `article_assets`, `metadata_fts`)에 **⑤ 실시간 작업 모니터링용 `pipeline_jobs`**와 **⑥ UI 초안 편집 및 ‘나의 결과물’ 저장용 `drafts_and_creations`** 테이블을 추가합니다.

```sql
-- (기존 1~4번 테이블: articles, article_metadata, article_assets, metadata_fts 동일 유지)

-- 5. [신규] 파이프라인 백그라운드 작업 및 실시간 진행률 모니터링 테이블
CREATE TABLE IF NOT EXISTS pipeline_jobs (
    job_id TEXT PRIMARY KEY,                  -- UUID 또는 타임스탬프 ID
    job_type TEXT NOT NULL,                   -- 'INGEST' | 'EXTRACT' | 'GENERATE' | 'STYLE_LEARN'
    status TEXT NOT NULL DEFAULT 'RUNNING',   -- 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
    total_items INTEGER DEFAULT 0,            -- 전체 대상 건수 (예: 4000)
    processed_items INTEGER DEFAULT 0,        -- 현재 완료 건수 (예: 1420)
    failed_items INTEGER DEFAULT 0,           -- 실패 건수
    current_doc_id TEXT DEFAULT '',           -- 현재 처리 중인 문서 ID 또는 단계명
    log_summary TEXT DEFAULT '',              -- 최근 로그 또는 에러 요약
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 6. [신규] 생성된 초안(Draft) 및 사용자가 수정 확정한 '나의 결과물(My Creation)' 관리 테이블
CREATE TABLE IF NOT EXISTS drafts_and_creations (
    creation_id TEXT PRIMARY KEY,             -- 예: 'cr_20261104_001'
    topic TEXT NOT NULL,                      -- 입력한 주제
    direction TEXT DEFAULT '',                -- 입력한 집필 방향/관점
    target_archetype TEXT DEFAULT '',         -- 선택한 글 구조 유형
    seed_doc_ids_json TEXT NOT NULL,          -- 사용된 Seed doc_id 리스트 (예: '["8194", "8195", "8204"]')
    blueprint_json TEXT NOT NULL,             -- SynthesisBlueprint JSON
    distilled_sheets_json TEXT NOT NULL,      -- 원문 탈색 재료 시트 JSON
    ai_draft_text TEXT NOT NULL,              -- [Before] AI가 최초 생성한 중립 초안 마크다운
    user_final_text TEXT DEFAULT '',          -- [After] 사용자가 UI에서 수정하여 저장한 '나의 결과물' 마크다운
    custom_notes TEXT DEFAULT '',             -- 이미지 재작성 메모 또는 편집 코멘트
    status TEXT NOT NULL DEFAULT 'DRAFT',     -- 'DRAFT' (초안 생성됨) | 'EDITING' (수정 중) | 'FINALIZED' (나의 결과물로 확정)
    used_for_style_learning INTEGER DEFAULT 0,-- 스타일 프로필 학습에 반영되었는지 여부 (0 or 1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalized_at TIMESTAMP
);
```

## 5. 핵심 모듈별 추가·개선 구현 명세

### 5.1 원문 문체 탈색기 (`src/synthesis/distiller.py`)

초안이 Seed의 문장과 포맷에 종속되는 문제를 해결하는 핵심 모듈입니다.

1. **동작 시점**: `retriever.py`가 2~3편의 Seed(`doc_id`)를 선정하고 `planner.py`가 `SynthesisBlueprint`를 만든 직후 실행됩니다.
2. **입출력**:
   * **입력**: 각 Seed의 정제 본문(`data/processed/texts/{doc_id}.md`)과 해당 Seed에 부여된 역할(`assigned_role`).
   * **처리**: LLM을 호출하여 원문의 에세이 톤, 질문형 소제목, 감성적 수식어, 플랫폼 고유 요약 박스를 모두 버리고, 오직 **건조한 개조식 명사구/불릿(`DistilledMaterialSheet`)** 형태로만 팩트·수치·인과관계·프롬프트 조건을 추출합니다.
   * **출력**: `List[DistilledMaterialSheet]` (이 객체만 `synthesizer.py`로 전달되며, **원문 `.md` 텍스트는 `synthesizer.py`에 절대 전달하지 않습니다**).

### 5.2 중립 초안 생성기 및 사후 스타일 어댑터 (`src/synthesis/synthesizer.py`, `style_learner.py`)

1. **초기 단계 (내 결과물 5편 미만 — Neutral Base Draft 모드)**:
   * `data/my_corpus/style_profile.json`이 아직 없을 때는 특정 스타일을 흉내 내지 않고, `SynthesisBlueprint`의 논리 흐름과 `DistilledMaterialSheet`의 팩트 재료를 결합해 **깔끔하고 구조적인 표준 마크다운 초안**을 생성합니다.
   * 원문 아티클의 특정 포맷(예: `'👀 바쁘다면 이거라도!'`)을 강제하던 규칙을 제거하여 Seed 포맷 복제를 원천 차단합니다.
   * 단, 본문 중간에 Seed의 시각 자료를 참고해 새로 그리거나 넣으면 좋은 위치에는 `> 🖼️ **[시각 자료 제안 - Seed #{doc_id} ({asset_id}) 참고]**: {캡션 및 새 주제에 맞춘 도식화 아이디어}` 형태의 콜아웃 블록을 삽입해 줍니다.

2. **성숙 단계 (내 결과물 5편 이상 축적 후 — My Style Profile 모드)**:
   * 사용자가 웹 UI에서 초안을 직접 고쳐 `status = 'FINALIZED'`로 저장한 결과물이 **5편 이상**이 되면, `style_learner.py`가 각 결과물의 **`ai_draft_text` (AI 초안) vs `user_final_text` (내가 고친 최종본)** 쌍을 비교(Diff)합니다.
   * *"사용자가 AI 초안의 어떤 표현을 지웠는가?"*, *"도입부와 소제목을 어떤 톤으로 바꿨는가?"*, *"문단 길이와 종결어미를 어떻게 통일했는가?"*를 추출하여 `data/my_corpus/style_profile.json`으로 저장합니다.
   * 이후 초안을 생성할 때는 이 `UserStyleProfile`과 내가 쓴 대표 최종본 1~2편의 발췌본을 Few-shot 레퍼런스로 주입하여 처음부터 **‘내 손길이 탄 것 같은 초안’**을 출력합니다.

## 6. 로컬 웹 UI 워크스페이스 상세 설계 (`src/ui/`)

복잡한 프론트엔드 빌드 없이 Python 환경에서 즉시 구동 가능한 **Streamlit 기반 4-Tab 웹 스튜디오 (`src/ui/app.py`)**로 구현합니다. `python run.py ui` 명령어로 실행하면 브라우저(`http://localhost:8501`)가 열립니다.

### 6.1 화면 구성 (4-Tab Architecture)

| 탭 이름 | 주요 기능 및 UI 컴포넌트 구성 | 연동 DB 및 파일 경로 |
| :--- | :--- | :--- |
| **Tab 1. 파이프라인 & 작업 모니터**<br>(`dashboard_view.py`) | • **실시간 작업 상태창**: 현재 실행 중인 수집(`INGEST`), 메타 추출(`EXTRACT`), 초안 생성(`GENERATE`) 작업의 진행률 바(`processed / total`), 성공/실패 건수, 최근 에러 로그 실시간 조회<br>• **인박스 원클릭 실행 버튼**: `[inbox 스캔 및 PDF 전처리 실행]`, `[미처리 문서 메타데이터 배치 추출 시작/이어받기]` 버튼 제공<br>• **Seed 인덱스 브라우저**: 저장된 4,000여 개 아티클을 카테고리/아키타입/키워드로 필터링하고 추출된 메타데이터와 이미지를 미리보기 | • `pipeline_jobs` 테이블 폴링<br>• `articles`, `article_metadata` 조회 |
| **Tab 2. 새 글 기획 & 초안 생성**<br>(`generator_view.py`) | • **기획 입력 폼**: 내가 쓸 글의 `주제(Topic)`, `집필 방향/관점(Direction)`, `선호 구조(Archetype, 선택)`, `내 스타일 프로필 적용 여부(체크박스)` 입력<br>• **Seed 매칭 프리뷰**: 초안을 바로 쓰기 전 `[Seed 후보 검색]`을 눌러 선별된 2~3편(소재 Seed / 관점 Seed / 구조 Seed)을 확인하고, 마음에 들지 않는 Seed는 다른 후보로 교체 가능<br>• **`[초안 합성 시작]` 버튼**: `Blueprint → DistilledSheet → Draft` 생성을 수행하고 완료 시 Tab 3(스튜디오)로 자동 연결 | • `retriever.py`, `distiller.py`, `synthesizer.py`<br>• `drafts_and_creations` (`status='DRAFT'`) |
| **Tab 3. 초안 편집 & Seed 이미지 스튜디오**<br>(`studio_view.py`) | • **좌측 패널 (Seed 재료 & 원본 이미지 갤러리)**:<br>  - 이번 초안에 사용된 Seed 2~3편의 핵심 논리 요약 카드<br>  - **Seed 원본 이미지/도표 뷰어**: 해당 Seed 문서들에서 추출된 모든 이미지(`article_assets`)를 썸네일 그리드 및 확대 모달로 표시 + 원본 캡션 표시<br>  - **커스텀 이미지 업로드/교체**: 원본 도표를 보고 내가 비슷하게 새로 그린 이미지를 업로드하면 `data/my_corpus/custom_assets/`에 저장되고 마크다운 이미지 태그(`![설명](경로)`)를 클립보드/에디터에 즉시 삽입<br>• **우측 패널 (실시간 마크다운 에디터 & 프리뷰)**:<br>  - 생성된 초안(`ai_draft_text`)을 자유롭게 수정하고 렌더링 결과를 실시간 확인<br>  - **`[임시 저장]`** 및 **`[나의 결과물로 확정 저장 (Save to My Corpus)]`** 버튼 제공 | • `article_assets` (`data/processed/assets/{doc_id}/`)<br>• `drafts_and_creations` (`user_final_text`, `status='FINALIZED'`)<br>• `data/my_corpus/articles/` |
| **Tab 4. 나의 결과물 & 스타일 학습소**<br>(`style_view.py`) | • **나의 결과물 아카이브**: 내가 수정 완료해 저장한 최종 글 목록 조회 및 마크다운 파일 다운로드<br>• **스타일 성숙도 게이지**: 현재 확정 저장된 내 결과물 개수 표시 (예: `현재 3/5편 달성 — 2편 더 저장하면 나만의 스타일 프로필을 추출할 수 있습니다` 프로그레스 바)<br>• **Before/After Diff 뷰어**: AI 초안(`ai_draft_text`)과 내 수정본(`user_final_text`)의 문장 수정 내역을 나란히 비교<br>• **`[내 스타일 프로필 추출/업데이트]` 버튼**: 5편 이상 누적 시 클릭 한 번으로 내 문체·구조·금기어 규칙(`style_profile.json`)을 생성하고 직접 편집·관리 가능 | • `drafts_and_creations` (`WHERE status='FINALIZED'`)<br>• `data/my_corpus/style_profile.json` |

## 7. CLI 및 웹 서버 실행 인터페이스 (`run.py`)

```bash
# 1. 로컬 웹 UI 워크스페이스 실행 (작업 모니터링, Seed 이미지 조회, 초안 편집, 내 결과물 저장 통합)
python run.py ui --port 8501

# 2. 특정 폴더(기본값: ./data/inbox)의 신규 아티클(PDF/MD/TXT) 전처리 및 원문/이미지 분리 저장
python run.py ingest --input-dir ./data/inbox --move-archive

# 3. 미처리 문서 대상 비동기 메타데이터 추출 및 SQLite FTS5 인덱스 갱신 (pipeline_jobs에 실시간 진행률 기록)
python run.py extract --concurrency 5 --model gpt-4o-mini

# 4. 원문 탈색(Distillation) 기반 중립 초안 생성 (내 스타일 프로필 존재 시 --use-my-style 옵션으로 적용 가능)
python run.py generate \
  --topic "비개발자 실무자의 사내 AI 자동화 도입기" \
  --direction "도구 자랑이 아니라 팀원들이 실제로 쓰게 만드는 운영과 신뢰 장치에 집중" \
  --count 3 \
  --use-my-style

# 5. 확정 저장된 '나의 결과물(5편 이상)' 기반으로 나만의 스타일 프로필 추출/갱신
python run.py learn-style
```

## 8. 핵심 프롬프트 템플릿 명세 (`src/extraction/prompts.py`)

### 8.1 원문 문체 탈색 프롬프트 (`MATERIAL_DISTILLATION_PROMPT` — 신설)

```text
당신은 원문 아티클에서 저자 특유의 문체, 수사법, 플랫폼 고정 포맷을 완전히 벗겨내고, 오직 '건조한 팩트, 수치, 인과관계, 실행 조건'만 발췌하는 데이터 정제기입니다.
초안 작성자가 원문의 문장이나 형식을 모방하지 못하도록, 아래 규칙에 따라 개조식 명사구 형태로만 재료 시트(DistilledMaterialSheet)를 추출하세요.

[탈색 및 발췌 규칙]
1. 문장 복사 절대 금지: 원문의 서술형 문장("~했습니다", "~하더라고요", "~해 보세요")을 그대로 가져오지 마세요. 모든 내용을 건조한 개조식 요약(예: "원인: 초기 유입 0명 발생 -> 조치: 무료 자산진단 도구 선제 배치 -> 결과: 5명 유입 중 3명 결제 전환")으로 변환하세요.
2. 플랫폼 고유 포맷 제거: 원문에 있는 요약 박스 제목(예: '바쁘다면 이거라도!'), 이모지 장식, 인사말, 홍보 문구는 모두 버리세요.
3. 알맹이 보존: 구체적인 숫자, 기간, 실패 원인과 해결 조건, 체크리스트의 판단 기준 등 '팩트의 정밀도'는 100% 유지하세요.
```

### 8.2 중립 초안 합성 프롬프트 (`DRAFT_SYNTHESIS_PROMPT` — 개선)

```text
당신은 주어진 [합성 설계도(Blueprint)]와 [탈색된 개조식 재료 시트(DistilledMaterialSheet)]만을 바탕으로, 사용자의 타깃 주제와 방향성에 맞는 완전히 새로운 글을 집필하는 전문 작가입니다.

[입력 데이터]
- 타깃 주제(Topic): {topic}
- 집필 방향 및 관점(Direction): {direction}
- 합성 설계도(Blueprint): {blueprint_json}
- 개조식 재료 시트(Distilled Materials): {distilled_sheets_json}
- 사용자 스타일 프로필(선택): {user_style_profile_or_neutral_guide}

[집필 원칙]
1. 독창적 서술과 구성: 재료 시트에 담긴 팩트, 에피소드 인과관계, 프레임워크는 적극 활용하되, 글의 호흡과 문장 구조는 타깃 주제({topic})와 방향({direction})에 맞춰 처음부터 새롭게 전개하세요.
2. 상투적 템플릿 배제: 기계적인 서두 요약이나 특정 플랫폼의 고정 엔딩 박스를 억지로 넣지 마세요. (단, 사용자 스타일 프로필이 제공된 경우 해당 프로필의 구조·어미·포맷 규칙을 최우선으로 따르세요.)
3. 시각 자료 삽입 가이드 표기: 본문 맥락상 Seed 문서에서 추출된 도표나 이미지를 참고해 새 그림/표를 넣으면 효과적인 위치에 `> 🖼️ **[시각 자료 제안 | Seed #{doc_id} - {asset_id}]**: {캡션 및 재구성 가이드}` 콜아웃을 명시하세요.
```

### 8.3 사용자 스타일 학습 프롬프트 (`STYLE_LEARNING_PROMPT` — 신설)

```text
아래 데이터는 AI가 생성한 [초안(Before)]과 사용자가 직접 문장과 구조를 고쳐 완성한 [나의 결과물(After)] 5편 이상의 비교 쌍(Diff Pairs)입니다.
사용자가 AI 초안의 어떤 점을 고쳤는지 정밀 분석하여, 앞으로 이 사용자의 문체와 포맷을 재현하기 위한 스타일 프로필(UserStyleProfile)을 추출하세요.

[분석 포인트]
1. 문체 및 어미 변화: 문장 길이, 단락 나누기 호흡, 선호하는 종결어미(예: '~합니다' vs '~해요' vs 평서형), 접속사 사용 습관.
2. 구조 및 포맷 변화: 도입부를 시작하는 방식, 소제목을 다는 스타일, 불릿이나 표를 배치하는 기준.
3. 삭제/기피 패턴(Forbidden Patterns): 사용자가 일관되게 지우거나 고쳐 쓴 AI 특유의 상투적 표현, 과장된 수식어, 불필요한 박스 포맷.
```

## 9. Antigravity 추가 구현 마일스톤 및 검증 기준 (v2.0 Upgrade Plan)

이미 v1.0 기본 파이프라인이 구현된 상태에서 Antigravity에 지시할 **v2.0 업그레이드 마일스톤(Milestone 5 ~ 7)**입니다.

| 단계 | 구현 모듈 | 세부 구현 과업 | 완료 검증 기준 (Verification Criteria) |
| :--- | :--- | :--- | :--- |
| **Milestone 5** | **원문 탈색(Distillation) 기반 합성 리팩토링**<br>(`distiller.py`, `synthesizer.py`, `prompts.py`) | • `DistilledMaterialSheet` 모델 및 `distiller.py` 구현<br>• `synthesizer.py`에서 Seed 원문(`.md`) 직접 주입을 제거하고 `Blueprint + DistilledMaterialSheet`만 주입하도록 변경<br>• 특정 플랫폼 포맷 강제 문구 제거 | • 생성된 초안이 Seed 원문의 문장 어미나 고정 요약 박스 포맷을 복제하지 않고, 새 주제와 방향성에 맞춘 독립적인 문장과 구조로 생성됨 |
| **Milestone 6** | **작업 상태 로깅 및 내 결과물 DB 확장**<br>(`db.py`, `repository.py`, `batch_extractor.py`) | • `pipeline_jobs` 및 `drafts_and_creations` 테이블 DDL 추가<br>• 수집/추출/합성 실행 시 `pipeline_jobs`의 `processed_items`, `status`, `log_summary` 실시간 업데이트 연동 | • 배치 작업 실행 중 DB 조회 시 현재 진행 건수와 상태(`RUNNING`/`COMPLETED`)가 실시간으로 갱신됨 |
| **Milestone 7** | **Streamlit 웹 스튜디오 & 스타일 학습 루프**<br>(`src/ui/app.py`, `style_learner.py`) | • 4-Tab 웹 UI 구현 (작업 모니터 / 초안 생성 / Seed 이미지 뷰어 & 마크다운 에디터 / 나의 결과물 & 스타일 학습소)<br>• `status='FINALIZED'` 결과물 5개 이상 누적 시 Diff 기반 `style_profile.json` 생성 및 합성기 연동 | • `python run.py ui` 실행 시 브라우저에서 Seed 원본 이미지 갤러리를 보며 초안을 수정해 '나의 결과물'로 저장할 수 있고, 5편 이상 저장 후 스타일 프로필 추출이 정상 동작함 |
