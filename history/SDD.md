# [SDD] 경량 메타데이터 인덱스 및 아티클 교차 합성 파이프라인 (Lightweight Seed Synthesis Engine)

* **문서 버전**: v1.0 (Antigravity 구현 명세서)
* **기반 문서**: `PRD.txt` (아티클 메타데이터 인덱싱 및 교차 합성 파이프라인)
* **런타임 환경**: Python 3.11+ / 로컬 파일시스템 및 SQLite3 (FTS5) / 무서버(Serverless) 경량 아키텍처

## 1. 시스템 설계 개요 및 핵심 아키텍처 원칙

본 문서는 로컬 폴더에 투입되는 약 4,000편 이상의 다양한 아티클(PDF, Markdown, TXT)을 전처리하여 **원문 텍스트, 시각 에셋(이미지/도표), 정형 메타데이터 인덱스로 분리 저장**하고, 사용자가 원하는 **주제(Topic)와 집필 방향(Direction/Angle)**을 입력했을 때 상호 보완적인 **Seed 아티클 2~3편을 교차 매칭하여 새로운 초안(Draft)을 합성**하는 파이프라인의 소프트웨어 상세 설계서(SDD)입니다.

### 1.1 핵심 설계 원칙 (Architectural Principles)

1. **Zero-Vector, Zero-Chunking 원칙**:
   * 무거운 벡터 DB 데몬이나 로컬 임베딩 모델을 일절 사용하지 않으며, 문서를 조각내지(Chunking) 않고 **단일 완결 문서 단위**로 맥락을 보존합니다.
2. **3-Tier 분리 저장소 아키텍처 (Separated Storage)**:
   * SQLite DB 파일 비대화를 막고 데이터 재활용성을 높이기 위해 **① 원본 보관소(`archive/`)**, **② 정제 본문 및 추출 이미지 저장소(`processed/`)**, **③ 초경량 메타데이터 검색 인덱스(`index/catalog.db`)**를 물리적으로 분리합니다.
3. **PDF 멀티모달 전처리 (Text + Visual Asset Extraction)**:
   * PDF 아티클의 경우 단순 텍스트 추출을 넘어 상·하단 반복 보일러플레이트(뉴스레터 배너, 저작권 문구 등)를 제거하고, 본문 내 핵심 도표·스크린샷 이미지를 추출하여 페이지 및 주변 캡션(`║ ... ©저자`)과 함께 매핑합니다.
4. **역할 기반 Seed 교차 합성 (Role-Based Cross-Synthesis)**:
   * 단순 유사 문서 상위 N개를 묶는 대신, **① 소재·사례 Seed(도메인 팩트/실패담)**, **② 관점·프레임워크 Seed(역발상 논리/실행 단계)**, **③ 서사·구조 Seed(글의 전개 형식)**로 역할을 분담하여 유기적인 초안을 생성합니다.

## 2. 디렉터리 구조 및 분리 저장소 설계

Antigravity가 생성해야 할 프로젝트 루트 및 데이터 저장소 레이아웃은 다음과 같습니다.

```text
seed-synthesis-engine/
├── pyproject.toml                 # 의존성 및 패키지 메타데이터 정의
├── .env.example                   # LLM API 키 및 기본 경로 환경변수 템플릿
├── config.yaml                    # 파이프라인 하이퍼파라미터 및 통제 어휘(Taxonomy) 설정
├── run.py                         # CLI 엔트리포인트
├── src/
│   ├── __init__.py
│   ├── config.py                  # 환경변수 및 YAML 설정 로더
│   ├── models.py                  # Pydantic v2 데이터 스키마 (메타데이터, 에셋, 합성 블루프린트)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── scanner.py             # 인박스 폴더 감시, 해시(SHA-256) 중복 검사, 파일 라우팅
│   │   ├── pdf_processor.py       # PDF 텍스트 정제, 보일러플레이트 제거, 이미지/캡션 분리 추출
│   │   └── text_normalizer.py     # MD/TXT 인코딩 정규화 및 섹션 헤더 구조화
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── llm_client.py          # 비동기 LLM 래퍼 (OpenAI/Anthropic/Gemini Structured Outputs)
│   │   ├── prompts.py             # 메타데이터 추출 및 초안 합성용 시스템/유저 프롬프트
│   │   └── batch_extractor.py     # Semaphore 동시성 제어, 지수 백오프, 체크포인트 기반 추출기
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                  # SQLite 커넥션, DDL 초기화, 트랜잭션 컨텍스트 매니저
│   │   ├── repository.py          # 메타데이터/에셋 CRUD 및 파일시스템 연동(processed/ 읽기·쓰기)
│   │   └── retriever.py           # FTS5 BM25 검색 + 역할별 Seed 다양성 리랭킹 엔진
│   └── synthesis/
│       ├── __init__.py
│       ├── planner.py             # 선별된 Seed 메타데이터 기반 '초안 설계도(Blueprint)' 생성
│       └── synthesizer.py         # 원문 Full-text 로드 후 롱컨텍스트 융합 초안 생성 및 파일 출력
├── data/                          # 런타임 데이터 디렉터리 (3-Tier 분리 저장)
│   ├── inbox/                     # [입력] 사용자가 새 아티클(PDF, MD, TXT)을 넣어두는 폴더
│   ├── archive/                   # [보관] 처리가 완료된 원본 파일 이동 보관 (확장자별/해시별)
│   ├── processed/                 # [분리 저장] 정제된 원문 및 추출 데이터
│   │   ├── texts/                 # {doc_id}.md (정제된 마크다운 원문 + 이미지 상대경로 태그)
│   │   ├── metadata/              # {doc_id}.json (추출된 메타데이터 개별 JSON 백업)
│   │   └── assets/                # {doc_id}/img_p{page}_{idx}.png 및 manifest.json
│   ├── index/
│   │   └── catalog.db             # [인덱스] SQLite3 + FTS5 경량 인덱스 DB (원문 본문 미포함, 경로만 참조)
│   └── outputs/                   # [출력] 생성된 최종 초안 마크다운 및 합성 리포트
└── tests/                         # 단위 및 통합 테스트
    ├── test_ingestion.py
    ├── test_retriever.py
    └── test_synthesizer.py
```

## 3. 데이터 파이프라인 흐름 (End-to-End Workflow)

파이프라인은 크게 **Phase 1(수집 및 전처리 분리 저장)**, **Phase 2(메타데이터 추출 및 인덱싱)**, **Phase 3(교차 검색 및 초안 합성)**의 3단계로 동작합니다.

| 단계 | 프로세스명 | 입력 데이터 | 핵심 처리 로직 | 출력 산출물 (저장 위치) |
| :--- | :--- | :--- | :--- | :--- |
| **Step 1** | **문서 수집 및 멀티모달 전처리**<br>(`ingest`) | `data/inbox/*`<br>(`.pdf`, `.md`, `.txt`) | • 파일명에서 고유 번호 추출(예: `8219_제목.pdf` → `doc_id: 8219`) 또는 SHA-256 해시 앞 10자리 부여<br>• PDF의 경우 페이지별 텍스트 추출 및 상하단 반복 광고/저작권 문구 제거<br>• PDF 내 일정 크기(`250x150px` 이상) 이상의 도표·스크린샷 이미지 추출 후 캡션과 매칭 | • 정제 본문: `data/processed/texts/{doc_id}.md`<br>• 추출 이미지: `data/processed/assets/{doc_id}/*`<br>• DB 레코드: `articles` 테이블 (`status='INGESTED'`) |
| **Step 2** | **메타데이터 배치 추출 및 FTS5 인덱싱**<br>(`extract & index`) | `texts/{doc_id}.md`<br>(`status='INGESTED'`) | • 미추출 문서만 조회(Checkpointing)<br>• 비동기 LLM 호출로 4계층 Seed 메타데이터(문제정의, 관점전환, 서사구조, 재료블록) 추출 및 Pydantic 검증<br>• 개별 JSON 저장 후 SQLite `article_metadata` 및 `metadata_fts` 가상 테이블 동기화 | • 메타 백업: `data/processed/metadata/{doc_id}.json`<br>• DB 인덱스: `data/index/catalog.db` (`status='INDEXED'`) |
| **Step 3** | **역할별 Seed 탐색 및 초안 합성**<br>(`generate`) | 사용자 쿼리:<br>`--topic` (주제)<br>`--direction` (방향/관점)<br>`--archetype` (형식) | • FTS5 BM25 검색으로 후보군(Top 15) 1차 필터링<br>• **교차 매칭 스코어링**: ① 도메인/사례 Seed 1~2편 + ② 관점/프레임워크 보완 Seed 1편 선정<br>• 선정된 2~3편의 `texts/{doc_id}.md` 전문과 `assets/{doc_id}/manifest.json`만 핀포인트 로드<br>• 합성 블루프린트 설계 후 최종 초안 작성 | • 초안 파일: `data/outputs/{timestamp}_{slug}.md`<br>• 합성 메타데이터 헤더(참조 Seed ID 및 차용 논리 명시) |

## 4. 데이터 모델 및 스키마 상세 설계 (`src/models.py`, `src/storage/db.py`)

### 4.1 Pydantic v2 스키마 (`src/models.py`)

기존 PRD의 4개 기본 필드를 확장하여, 새로운 글을 창작할 때 **‘어떤 관점(Reframing)을 빌려올지’**, **‘어떤 글쓰기 구조(Archetype)를 따를지’**, **‘어떤 실무 재료(에피소드/체크리스트/프롬프트)를 발췌할지’**를 판단할 수 있도록 구성합니다.

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ArticleArchetype(str, Enum):
    TRIAL_AND_ERROR_RETRO = "trial_and_error_retro"       # 1인칭 시행착오 및 프로젝트 회고형 (예: 첫 판매기, 부업 시작기)
    STEP_BY_STEP_TUTORIAL = "step_by_step_tutorial"       # 실전 구축 및 단계별 튜토리얼형 (예: 슬랙 봇 만들기, 클로드 배포)
    FRAMEWORK_CHECKLIST = "framework_checklist"           # 실무 프로세스 및 체크리스트 제안형 (예: D-90 역산 기획, 독서 루틴)
    CASE_STUDY_WORKSHOP = "case_study_workshop"           # 다중 사례 분석 및 실습 워크숍형 (예: 커리어 피봇 포트폴리오)
    BRAND_INTERVIEW_QA = "brand_interview_qa"             # 브랜드/창업가 스토리 강연 및 Q&A형 (예: 불닭 BM, 단하주단)
    TEMPLATE_CURATION = "template_curation"               # 로드맵 기반 템플릿/도구 모음집형 (예: 신입 50일 생존 템플릿)

class ReusableAssetType(str, Enum):
    PROMPT_TEMPLATE = "prompt_template"                   # 복붙 가능한 AI 프롬프트/지시문
    CHECKLIST_TABLE = "checklist_table"                   # 점검표 및 자가진단 리스트
    BEFORE_AFTER_COMPARISON = "before_after_comparison"   # 수정 전/후 비교 사례
    QUANTITATIVE_METRICS = "quantitative_metrics"         # 실제 매출, 전환율, 소요 시간 등 정량 수치
    FAILURE_EPISODE = "failure_episode"                   # 구체적 실패/반려/시행착오 에피소드
    STEP_DIAGRAM = "step_diagram"                         # 프로세스 도식 및 퍼널 설계도

class VisualAssetItem(BaseModel):
    asset_id: str = Field(..., description="이미지 파일 식별자 (예: img_p04_01)")
    page_no: int = Field(..., description="원본 PDF 페이지 번호")
    file_path: str = Field(..., description="processed/assets/ 내 상대 경로")
    caption: str = Field(default="", description="이미지 하단 또는 주변에서 추출된 캡션 텍스트")
    width: int
    height: int

class ArticleMetadata(BaseModel):
    # 1. 타깃 및 문제의식 (Target & Problem)
    target_audience: str = Field(
        ..., description="이 글이 가장 유효하게 작용하는 구체적 타깃 독자 페르소나 및 처한 상황 (1~2문장)"
    )
    core_problem: str = Field(
        ..., description="독자가 겪고 있는 표면적 막막함 또는 글이 해결하려는 핵심 질문 (1~2문장)"
    )
    
    # 2. 관점 전환 및 핵심 테제 (Perspective & Reframing Seed)
    reframing_logic: str = Field(
        ..., description="통념을 뒤집는 관점의 전환 공식 ('문제가 A인 줄 알았는데 실제로는 B였다' 형태, 1~2문장)"
    )
    core_thesis: str = Field(
        ..., description="글 전체를 관통하는 단 하나의 핵심 결론 문장"
    )
    
    # 3. 서사 구조 및 해결 프레임워크 (Structure & Framework Seed)
    article_archetype: ArticleArchetype = Field(
        ..., description="글의 전체 전개 방식 및 장르 유형"
    )
    hook_strategy: str = Field(
        ..., description="도입부에서 독자의 시선을 끄는 방식 (예: 수치 공개, 실패담 고백, 자가진단 체크리스트 등)"
    )
    solution_framework: List[str] = Field(
        ..., min_length=2, max_length=6,
        description="글이 제시하는 단계별 실행 방법론 또는 핵심 프레임워크 (3~5개 항목 리스트)"
    )
    
    # 4. 재사용 재료 및 분류 태그 (Material & Taxonomy Seed)
    notable_episodes: List[str] = Field(
        ..., min_length=1, max_length=4,
        description="새 글에 인용하기 좋은 구체적 사례, 시행착오 에피소드, 정량적 실험 결과 요약 (1~3개)"
    )
    reusable_asset_types: List[ReusableAssetType] = Field(
        default_factory=list,
        description="본문 내 포함된 실무 도구/근거 블록 유형 리스트"
    )
    primary_category: str = Field(
        ..., description="대분류 도메인 (예: 업무스킬, 서비스기획/AI, 마케팅/브랜딩, 커리어/이직, 부업/수익화, 자기관리)"
    )
    topic_tags: List[str] = Field(
        ..., min_length=3, max_length=7,
        description="글의 핵심 소재 및 키워드 태그 (3~7개)"
    )

class SynthesisBlueprint(BaseModel):
    """초안 작성 전 선별된 Seed들을 어떻게 엮을지 정의하는 합성 설계도"""
    proposed_title: str = Field(..., description="새로 작성할 아티클의 가제")
    target_reader_definition: str = Field(..., description="새 글의 타깃 독자 및 핵심 페인포인트")
    synthesized_reframing: str = Field(..., description="Seed들의 관점을 결합하여 도출한 새 글만의 핵심 관점 전환 명제")
    role_assignments: List[str] = Field(..., description="각 Seed 문서(doc_id)에서 차용할 구체적 요소 (문제제기/프레임워크/사례 등) 명시")
    section_outline: List[str] = Field(..., description="새 글의 섹션별 소제목 및 핵심 내용 구성안 (4~6개 섹션)")
```

### 4.2 SQLite3 및 FTS5 데이터베이스 스키마 (`src/storage/db.py`)

원문 전체 텍스트(`raw_text`)는 `data/processed/texts/{doc_id}.md` 파일로 분리 저장하고, DB에는 **파일 경로 포인터와 요약/메타데이터**만 두어 4,000건 이상의 데이터에서도 DB 파일 크기를 15~30MB 이내로 유지합니다.

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. 문서 레지스트리 및 전처리 상태 관리 테이블
CREATE TABLE IF NOT EXISTS articles (
    doc_id TEXT PRIMARY KEY,                  -- 파일 고유 번호(예: '8219') 또는 해시 기반 ID
    title TEXT NOT NULL,                      -- 정제된 문서 제목
    author TEXT DEFAULT '',                   -- 저자명 (추출 가능 시)
    published_date TEXT DEFAULT '',           -- 발행일 (YYYY-MM-DD, 추출 가능 시)
    source_format TEXT NOT NULL,              -- 'pdf', 'md', 'txt'
    original_path TEXT NOT NULL,              -- data/archive/ 내 원본 파일 경로
    processed_text_path TEXT NOT NULL,        -- data/processed/texts/{doc_id}.md 경로
    assets_dir_path TEXT DEFAULT '',          -- data/processed/assets/{doc_id}/ 경로
    content_hash TEXT NOT NULL UNIQUE,        -- 중복 방지용 SHA-256 해시
    char_count INTEGER NOT NULL,              -- 정제된 본문 글자 수
    image_count INTEGER DEFAULT 0,            -- 추출된 유효 이미지/도표 수
    status TEXT NOT NULL DEFAULT 'INGESTED',  -- 'INGESTED' | 'INDEXED' | 'FAILED'
    error_msg TEXT DEFAULT '',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP
);

-- 2. 구조화된 Seed 메타데이터 테이블
CREATE TABLE IF NOT EXISTS article_metadata (
    doc_id TEXT PRIMARY KEY,
    primary_category TEXT NOT NULL,
    article_archetype TEXT NOT NULL,
    target_audience TEXT NOT NULL,
    core_problem TEXT NOT NULL,
    reframing_logic TEXT NOT NULL,
    core_thesis TEXT NOT NULL,
    hook_strategy TEXT NOT NULL,
    solution_framework_json TEXT NOT NULL,    -- JSON Array String
    notable_episodes_json TEXT NOT NULL,      -- JSON Array String
    reusable_assets_json TEXT NOT NULL,       -- JSON Array String
    topic_tags_json TEXT NOT NULL,            -- JSON Array String
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id) ON DELETE CASCADE
);

-- 3. 추출된 이미지/도표 에셋 메타 테이블
CREATE TABLE IF NOT EXISTS article_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,                   -- 예: 'img_p04_01'
    page_no INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    caption TEXT DEFAULT '',
    width INTEGER,
    height INTEGER,
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id) ON DELETE CASCADE
);

-- 4. 초고속 전문 검색을 위한 FTS5 가상 테이블 (unicode61 토크나이저 사용)
CREATE VIRTUAL TABLE IF NOT EXISTS metadata_fts USING fts5(
    doc_id UNINDEXED,
    title,
    primary_category,
    target_audience,
    core_problem,
    reframing_logic,
    core_thesis,
    solution_framework,
    notable_episodes,
    topic_tags,
    asset_captions,
    tokenize = 'unicode61 remove_diacritics 2'
);
```

## 5. 핵심 모듈별 상세 구현 명세 (Module Specifications)

### 5.1 수집 및 PDF 멀티모달 전처리 모듈 (`src/ingestion/`)

1. **파일 식별자(`doc_id`) 및 메타 헤더 파싱 (`scanner.py`)**:
   * 파일명이 `{숫자}_{제목}.pdf` 패턴(예: `8219_그때 그거 어디서 정했죠...pdf`)인 경우 정규식 `^(\d+)_(.+)\.(pdf|md|txt)$`으로 `doc_id`와 초기 `title`을 추출합니다. 숫자 접두사가 없는 파일은 본문 SHA-256 해시 앞 8자리를 `doc_id`로 부여합니다.
   * `articles.content_hash`를 조회하여 이미 동일한 해시가 존재하면 중복 수집을 건너뜁니다(`--force` 옵션 시 재처리).

2. **PDF 텍스트 및 이미지 분리 추출기 (`pdf_processor.py`)**:
   * **라이브러리**: `pypdf`/`pdfplumber`(텍스트 및 레이아웃) + `pypdfium2` 또는 `PyMuPDF(fitz)`(임베디드 이미지 추출).
   * **보일러플레이트 정제 (Boilerplate Stripping)**:
     * 아티클 PDF 상·하단에 반복 출현하는 고정 배너 문구(예: `"업무 고민 나누면, 해결책이 온다! 퍼블리 뉴스레터 로 꾸준히 성장하기"`, `"프로필 더 보기"`, `"©모든 저작권은 해당 콘텐츠 제공자 또는..."`, 단순 페이지 번호 등)를 정규식 필터로 제거합니다.
     * 1페이지 상단에서 `저자 {이름}`, `* 발행일: YYYY.MM.DD` 또는 `[콘텐츠 발행일: YYYY.MM.DD]` 패턴을 감지해 `author`, `published_date` 메타데이터로 분리 저장합니다.
   * **시각 에셋(이미지/표) 및 캡션 추출**:
     * 페이지 내 임베디드 이미지 중 배너·아이콘·프로필 아바타를 걸러내기 위해 **가로 250px 이상, 세로 150px 이상**이면서 종횡비가 극단적이지 않은(`0.2 < w/h < 5.0`) 유효 이미지만 `data/processed/assets/{doc_id}/img_p{page:02d}_{idx:02d}.png`로 저장합니다.
     * 이미지 직하단 텍스트 블록 중 `║` 기호나 `©` 기호가 포함된 줄(예: `║ 결과와 출처를 붙여 답해요. ©하루`)을 해당 이미지의 `caption`으로 매핑합니다.
     * 정제된 마크다운 본문(`data/processed/texts/{doc_id}.md`)의 해당 페이지 위치에 `![{caption}](../assets/{doc_id}/img_p{page:02d}_{idx:02d}.png)` 마크다운 링크를 삽입하여 원문 읽기와 시각 자료 참조가 동시에 가능하도록 구성합니다.

### 5.2 비동기 메타데이터 배치 추출기 (`src/extraction/batch_extractor.py`)

1. **체크포인트 기반 이어받기 (Fault-Tolerant Checkpointing)**:
   * 시작 시 `SELECT doc_id, title, processed_text_path FROM articles WHERE status = 'INGESTED' OR status = 'FAILED'` 쿼리로 미완료 문서만 큐에 적재합니다.
   * 각 문서의 추출이 성공할 때마다 즉시:
     1. `data/processed/metadata/{doc_id}.json` 파일을 기록하고,
     2. SQLite 트랜잭션으로 `article_metadata`와 `metadata_fts`를 `INSERT OR REPLACE`한 뒤,
     3. `articles.status = 'INDEXED'`로 갱신합니다.
   * 이를 통해 4,000편 처리 도중 프로세스가 강제 종료되거나 네트워크가 끊겨도 재실행 시 단 1건의 유실이나 중복 과금 없이 이어받기가 가능합니다.
2. **비동기 동시성 및 Rate Limit 제어**:
   * `asyncio.Semaphore(max_concurrency)`(기본값 `5~10`, CLI 옵션으로 조정 가능)로 동시 요청 수를 제한합니다.
   * API 호출 실패(429 Rate Limit, 5xx Server Error, Timeout) 시 `tenacity` 또는 커스텀 지수 백오프(Exponential Backoff: `2s → 4s → 8s → 16s`, 최대 4회 재시도)를 수행합니다.

### 5.3 경량 인덱스 및 역할 기반 교차 검색 엔진 (`src/storage/retriever.py`)

사용자가 `--topic` (내가 쓰고 싶은 주제)와 선택적 `--direction` (관점/방향성), `--archetype` (원하는 글의 형식)을 입력했을 때, **상호 보완적인 2~3편의 Seed 아티클**을 선별하는 2단계 검색 알고리즘입니다.

1. **Stage 1 — FTS5 다중 가중치 후보군 추출 (Top-K Retrieval, K=15)**:
   * 입력된 `topic`과 `direction`에서 조사/불용어를 제거한 핵심 키워드를 추출하여 `metadata_fts`에 `MATCH` 쿼리를 실행합니다.
   * SQLite FTS5 내장 `bm25()` 함수를 활용하여 컬럼별 가중치를 차등 부여합니다:
     * `title` (2.0), `core_problem` (2.5), `reframing_logic` (3.0), `solution_framework` (2.0), `topic_tags` (2.5), `notable_episodes` (1.5).
   * FTS5 매칭 결과가 부족할 경우(예: 추상적인 주제어), `topic_tags` 및 `primary_category` 기반 `LIKE` 폴백 검색을 결합해 최소 10~15개의 후보군(`Candidate Pool`)을 확보합니다.

2. **Stage 2 — 역할 분담 및 다양성 스코어링 (Complementary Seed Selection)**:
   * 후보군 15개 메타데이터를 바탕으로 중복된 내용의 글이 뽑히지 않도록 **역할별 그리디 선택(Greedy Diversity Selection) 또는 경량 LLM 리랭킹**을 수행하여 최종 2~3편을 확정합니다:
     * **Seed #1 (Domain & Case Seed / 소재·사례 중심)**: 사용자의 `--topic`과 BM25 유사도가 가장 높고, `notable_episodes`나 `quantitative_metrics`가 풍부한 아티클 1편 선정.
     * **Seed #2 (Perspective & Framework Seed / 관점·프레임워크 중심)**: 후보군 중 Seed #1과 **프레임워크/카테고리 중복도가 낮으면서**(`jaccard_similarity(tags_1, tags_2) < 0.5` 또는 상이한 `article_archetype`), 사용자의 `--direction`에 부합하는 강력한 `reframing_logic`과 `solution_framework`를 가진 아티클 1편 선정.
     * **Seed #3 (Structure & Asset Seed / 구조·실무도구 보완, `--count 3`일 때)**: 사용자가 지정한 `--archetype`과 일치하거나, 실무 활용도를 높여줄 `prompt_template`, `checklist_table`, `before_after_comparison` 에셋을 보유한 아티클 1편 추가 선정.

### 5.4 롱컨텍스트 초안 합성기 (`src/synthesis/`)

선별된 2~3편의 Seed를 단순 요약·나열하지 않고, **하나의 일관된 관점과 호흡을 가진 새로운 초안**으로 창조하기 위해 **2-Step 합성 파이프라인**을 적용합니다.

1. **Step 1 — 합성 설계도(`SynthesisBlueprint`) 생성 (`planner.py`)**:
   * 선별된 2~3편의 **메타데이터(`ArticleMetadata`)만** 먼저 LLM에 투입하여, 사용자의 `--topic`과 `--direction`을 달성하기 위해 각 Seed에서 무엇을 가져와 어떻게 결합할지 `SynthesisBlueprint` JSON을 생성합니다.
   * **합성 공식 예시**:
     * *Seed #1(`8194` AI 서비스 첫 판매기)*의 **‘초기 유입 0건 실패담과 무료 가치 우선 제공 퍼널’** 사례 +
     * *Seed #2(`8195` 독서 기록 치트키)*의 **‘의지가 아니라 마찰의 문제이므로 1초 컷 가짜 성취감을 설계하라’**는 관점 전환 논리 +
     * *Seed #3(`8204` 연말 프로모션 D-90 역산 기획)*의 **‘실행일 기준 역산 체크리스트’** 구조를 결합.

2. **Step 2 — 원문 핀포인트 로드 및 본문 집필 (`synthesizer.py`)**:
   * 확정된 `SynthesisBlueprint`와 함께, 선별된 2~3편의 정제 원문(`data/processed/texts/{doc_id}.md`) 및 에셋 캡션 목록(`article_assets`)을 프롬프트에 주입합니다.
   * **집필 가드레일 (Writing Guardrails)**:
     * 서론에서 공허한 인사말이나 기계적인 요약을 배제하고, 구체적인 상황·수치·질문(Hook)으로 즉시 시작할 것.
     * Seed 원문의 생생한 디테일(구체적 숫자, 겪은 시행착오, 실제 프롬프트/체크리스트 양식)은 살리되, 논리 전개는 반드시 사용자의 타깃 주제(`--topic`)와 방향(`--direction`)에 맞춰 재해석(Transcreation)할 것.
     * 본문 마지막에는 원문 아티클들처럼 독자가 즉시 실행할 수 있는 **요약 박스(`👀 바쁘다면 이거라도!` 또는 `✅ 오늘 바로 시작할 체크리스트`)**와, 참조한 Seed 이미지/도표를 활용할 수 있는 위치 제안을 포함할 것.
   * **산출물 저장**: `data/outputs/{YYYYMMDD_HHMMSS}_{topic_slug}.md`에 YAML Frontmatter(사용된 Seed `doc_id` 목록, 적용된 `reframing_logic`, 생성 일시)와 함께 본문 초안을 저장합니다.

## 6. CLI 인터페이스 명세 (`run.py`)

`typer`를 사용하여 직관적인 명령어 체계를 구성합니다. 개별 단계 실행과 원클릭 통합 실행을 모두 지원합니다.

```bash
# 1. 특정 폴더(기본값: ./data/inbox)의 신규 아티클(PDF/MD/TXT) 전처리 및 원문/이미지 분리 저장
python run.py ingest --input-dir ./data/inbox --move-archive

# 2. 미처리 문서 대상 비동기 메타데이터 추출 및 SQLite FTS5 인덱스 갱신 (이어받기 자동 지원)
python run.py extract --concurrency 5 --model gpt-4o-mini

# 3. 저장된 메타데이터 인덱스 기반 검색 테스트 (원문 합성 없이 매칭되는 Seed 후보군과 선정 이유만 확인)
python run.py search --topic "사이드 프로젝트 지속하기" --direction "완벽주의를 버리고 마찰을 줄이는 루틴 설계" --count 3

# 4. 주제와 방향성에 맞춘 Seed 교차 선별 + 초안(Draft) 생성
python run.py generate \
  --topic "비개발자 실무자의 사내 AI 자동화 도입기" \
  --direction "도구 자랑이 아니라 팀원들이 실제로 쓰게 만드는 운영과 신뢰 장치에 집중" \
  --archetype "trial_and_error_retro" \
  --count 3 \
  --output-dir ./data/outputs

# 5. 전체 파이프라인 원클릭 실행 (신규 파일 수집 → 메타 추출/인덱싱 → 초안 생성)
python run.py pipeline --input-dir ./data/inbox --topic "..." --direction "..."
```

## 7. 핵심 프롬프트 템플릿 명세 (`src/extraction/prompts.py`)

Antigravity가 `prompts.py`에 그대로 구현할 시스템 프롬프트 규격입니다.

### 7.1 메타데이터 추출 프롬프트 (`METADATA_EXTRACTION_PROMPT`)

```text
당신은 아티클의 표면적 정보뿐만 아니라 '설득 논리', '글쓰기 구조', '재사용 가능한 실무 재료'를 해부하는 콘텐츠 아키텍트입니다.
주어진 아티클 전문을 읽고, 향후 다른 주제의 글을 창작할 때 'Seed(씨앗)'로 활용할 수 있도록 지정된 JSON 스키마(ArticleMetadata)에 맞춰 메타데이터를 추출하세요.

[추출 원칙]
1. reframing_logic (관점 전환): 이 글이 독자의 기존 통념을 어떻게 뒤집는지 포착하세요. 반드시 "흔히 A라고 생각하지만, 실제로는 B의 문제다(따라서 C해야 한다)"의 인과가 드러나야 합니다.
2. solution_framework (해결 프레임워크): 추상적인 덕담이 아니라, 다른 도메인에도 이식할 수 있는 구체적인 단계별 실행 로직(3~5단계)으로 요약하세요.
3. notable_episodes (핵심 사례/에피소드): 저자가 직접 겪은 구체적인 실패담, 반전 사례, 실험 수치(예: "유입 0명에서 무료 진단 도구 도입 후 5명 중 3명 결제")를 왜곡 없이 구체적으로 적으세요.
```

### 7.2 교차 합성 초안 생성 프롬프트 (`DRAFT_SYNTHESIS_PROMPT`)

```text
당신은 현업 전문가의 생생한 경험과 날카로운 프레임워크를 결합해 독자의 행동을 이끌어내는 수석 에디터입니다.
아래 제공된 [합성 설계도(Blueprint)]와 [선별된 Seed 아티클 원문 2~3편]을 재료로 삼아, 사용자가 요청한 주제와 방향성에 맞는 완성도 높은 아티클 초안을 작성하세요.

[사용자 요청]
- 타깃 주제(Topic): {topic}
- 집필 방향 및 관점(Direction): {direction}
- 목표 아키타입(Archetype): {archetype}

[합성 및 집필 규칙]
1. 기계적 짜깁기 금지: Seed A 요약 다음에 Seed B 요약을 이어 붙이지 마세요. [합성 설계도]에 정의된 단일 관점(synthesized_reframing)을 중심으로 글 전체가 한 사람의 일관된 호흡으로 읽혀야 합니다.
2. 구체성 이식: Seed 원문에 등장하는 구체적인 검증 방식, 프롬프트 구조, 체크리스트 표, 시행착오의 디테일을 새 주제에 맞게 변주하거나 레퍼런스 사례로 자연스럽게 녹여내세요.
3. 시각 에셋 및 실무 도구 배치: 본문 흐름상 표(Markdown Table), 체크리스트 박스, 또는 Seed에서 추출된 이미지/도표 참고 위치([참고 에셋: {doc_id}/{asset_id} - {caption}])를 적재적소에 배치하세요.
4. 마무리 요약: 글 하단에는 핵심 실행 지침 4~6줄을 요약한 '👀 바쁘다면 이거라도!' 섹션을 반드시 포함하세요.
```

## 8. Antigravity 구현 마일스톤 및 검증 기준 (Implementation Plan & DoD)

Antigravity 에이전트가 본 SDD를 입력받아 순차적으로 코드를 작성하고 검증할 단계별 체크리스트입니다.

| 단계 | 구현 모듈 | 세부 구현 과업 | 완료 검증 기준 (Verification Criteria) |
| :--- | :--- | :--- | :--- |
| **Milestone 1** | **프로젝트 초기화 및 DB/모델 계층**<br>(`models.py`, `db.py`, `repository.py`) | • `pyproject.toml` 구성 (`pydantic>=2.0`, `pypdf`, `pypdfium2`, `pillow`, `typer`, `litellm` 또는 `openai`/`google-genai`, `tenacity`)<br>• SQLite 테이블 3종 및 `metadata_fts` 가상 테이블 생성 스크립트 구현 | • `pytest tests/test_storage.py` 실행 시 `catalog.db` 생성 및 FTS5 한글/영문 키워드 `MATCH` 쿼리가 50ms 이내 정상 동작함 |
| **Milestone 2** | **멀티모달 수집 및 PDF 전처리기**<br>(`scanner.py`, `pdf_processor.py`) | • `data/inbox/` 내 PDF/MD/TXT 스캔 및 SHA-256 중복 체크<br>• PDF 본문 텍스트 정제 + 유효 이미지(`>=250x150px`) 분리 저장 + 캡션 매칭 구현 | • 샘플 PDF 10종 투입 시 `data/processed/texts/{doc_id}.md`와 `data/processed/assets/{doc_id}/`에 정제 본문 및 이미지가 누락 없이 분리 저장됨 |
| **Milestone 3** | **비동기 메타데이터 배치 추출기**<br>(`llm_client.py`, `batch_extractor.py`) | • Structured Outputs 기반 `ArticleMetadata` 추출 구현<br>• `Semaphore` 동시성 제어 및 문서 단위 즉시 커밋(Checkpointing) 구현 | • 추출 중 강제 중단 후 재실행 시 이미 `INDEXED` 상태인 문서는 건너뛰고 미처리 문서만 정확히 이어받아 완료함 |
| **Milestone 4** | **교차 검색 및 초안 합성기**<br>(`retriever.py`, `planner.py`, `synthesizer.py`, `run.py`) | • FTS5 BM25 검색 + 역할별(소재/관점/구조) 보완 Seed 선정 로직 구현<br>• `SynthesisBlueprint` 생성 후 롱컨텍스트 초안 마크다운 출력 CLI 완성 | • `python run.py generate --topic "..." --direction "..."` 실행 시 상호 보완적인 Seed 2~3편이 선별되고, 구조화된 초안 `.md` 파일이 `data/outputs/`에 생성됨 |
