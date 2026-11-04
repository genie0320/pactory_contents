# [PRD] 아티클 메타데이터 인덱싱 및 교차 합성 파이프라인 (Lightweight Synthesis Engine)

## 1. 프로젝트 개요

* **프로젝트명**: 경량 메타데이터 기반 아티클 교차 합성 파이프라인 구축
* **배경 및 목적**:
* 로컬 환경에 보관된 약 4,000편의 완결형 아티클(편당 5~10분 분량)을 벡터 DB나 텍스트 청킹(Chunking) 없이 구조화.
* 글의 맥락 훼손 없이 3대 메타데이터를 추출하여 초경량 인덱스를 구축하고, 특정 주제에 대해 상호 보완적인 아티클 2~3편을 선별하여 롱컨텍스트 LLM으로 합성 초안을 생성하는 자동화 파이프라인 개발.


* **주요 타깃 산출물**: Python 기반 파이프라인 패키지(CLI 및 모듈 형태)

---

## 2. 시스템 아키텍처 및 데이터 흐름

```
[4,000편 아티클 (MD/TXT)] 
       │
       ▼
[1. 메타데이터 배치 추출기] ──(비동기 LLM 호출 + Checkpoint)──► [Pydantic 검증]
       │
       ▼
[2. 경량 인덱스 저장소 (SQLite + FTS5)]
       │
       ▼  ◄── 사용자 쿼리 / 타깃 주제 입력
[3. 교차 검색 및 매칭 엔진]
       │
       ├─► 메타데이터 기반 연관 아티클 2~3편 전문(Full-text) 로드
       ▼
[4. 롱컨텍스트 합성 생성기] ──(LLM 프롬프트 주입)──► [최종 융합 콘텐츠 초안]

```

---

## 3. 세부 기능 요구사항 (Functional Requirements)

### FR-1. 데이터 수집 및 전처리 모듈 (`ingestion.py`)

* **입력 데이터**: 지정 디렉터리 내 아티클 파일군 (Markdown, TXT 등 약 4,000개).
* **기능**:
* 파일 읽기, 중복 제거(해시 기반), 비정상 인코딩 및 불필요한 특수문자 정제.
* 아티클 고유 ID(`doc_id`), 파일 경로, 원문 텍스트, 글자 수를 포함하는 기본 레코드 생성.
* 전체 텍스트를 청킹하지 않고 단일 문서 단위로 유지.



### FR-2. 메타데이터 배치 추출기 (`extractor.py`)

* **기능**:
* 4,000편의 본문을 LLM에 전달하여 정형 메타데이터(3요소 + 태그)를 JSON 구조로 추출.
* Structured Outputs(Pydantic Schema)를 강제하여 파싱 실패 방지.


* **추출 스키마**:
* `core_problem` (핵심 문제의식): 글에서 제기하는 핵심 질문 또는 문제 정의 (1~2문장)
* `target_audience` (대상 독자): 글이 가장 유효하게 작용하는 타깃 페르소나 (1~2문장)
* `solution_framework` (해결 프레임워크): 글이 제시하는 3~4단계 실행 로직이나 방법론 (요약 리스트)
* `topic_tags` (주제 태그): 비즈니스, 커뮤니케이션, 기획 등 대분류/소분류 태그 (3~5개)


* **운영 제약 및 예외 처리**:
* **체크포인트(Checkpointing)**: 작업 중단 시 재실행할 수 있도록 처리 완료된 `doc_id`는 즉시 저장하고, 미처리 문서만 선별하여 이어받기 지원.
* **비동기 배치 및 Rate Limit 제어**: `asyncio` 기반 동시 호출 수(Semaphore) 제어 및 API 재시도(Exponential Backoff) 적용.



### FR-3. 경량 인덱스 저장소 및 검색 모듈 (`indexer.py`, `retriever.py`)

* **저장소**: 서버 부하가 없는 파일 기반 임베디드 DB(**SQLite**) 사용. 외부 DB 서버 설치 배제.
* **테이블 구조**:
1. `articles`: 원문 메타정보 및 본문 저장 (`doc_id`, `file_path`, `raw_text`, `created_at`)
2. `article_metadata`: 추출된 구조화 데이터 저장 (`doc_id`, `core_problem`, `target_audience`, `solution_framework`, `tags`)
3. `metadata_fts`: 빠른 키워드/개념 매칭을 위한 SQLite **FTS5(Full-Text Search)** 가상 테이블


* **검색 엔진 로직**:
* 단일 쿼리 입력 시, 메타데이터 필드(문제의식, 독자, 프레임워크) 대상 BM25 기반 텍스트 매칭.
* **교차 후보군 추출**: 타깃 주제와 맞닿아 있으면서 서로 상이한 프레임워크를 가진 아티클 2~3편을 스코어링하여 최종 선정.



### FR-4. 롱컨텍스트 합성 생성기 (`synthesizer.py`)

* **기능**:
* 선별된 2~3편의 아티클 전문(Full-text)을 로드.
* 합성 템플릿 프롬프트에 원문 전문과 출력 형식을 결합하여 LLM에 전달.


* **합성 전략**:
* 단순 짜깁기가 아닌 'A 아티클의 문제 제기 + B 아티클의 해법 프레임워크' 융합 지시.
* 불필요한 서두와 기계적 요약을 배제하고 고밀도 인사이트 중심의 초안 작성 지시.


* **결과 저장**: 생성된 초안을 타깃 메타데이터와 함께 마크다운 파일로 내보내기.

### FR-5. 실행 인터페이스 (`main.py` / CLI)

* Typer 또는 Click 기반의 직관적인 CLI 명령어 제공.
* `python run.py extract --input-dir ./articles` (배치 메타데이터 추출)
* `python run.py index` (SQLite FTS 인덱스 빌드)
* `python run.py generate --topic "기획자의 데이터 기반 커뮤니케이션" --count 2` (교차 검색 후 합성 초안 출력)



---

## 4. 데이터 스키마 정의 (Pydantic & SQL)

### 4.1. Metadata Extraction Schema (Pydantic v2)

```python
from pydantic import BaseModel, Field
from typing import List

class ArticleMetadata(BaseModel):
    core_problem: str = Field(
        ..., description="글이 해결하고자 하는 핵심 문제의식 및 발단 (1~2문장)"
    )
    target_audience: str = Field(
        ..., description="이 인사이트가 가장 필요한 대상 독자 페르소나"
    )
    solution_framework: List[str] = Field(
        ..., description="글에서 제시하는 핵심 실행 방법론 또는 단계별 프레임워크 (3~5개 항목)"
    )
    topic_tags: List[str] = Field(
        ..., description="글의 도메인 및 주제를 관통하는 핵심 키워드 태그 (3~5개)"
    )

```

### 4.2. SQLite Schema DDL

```sql
CREATE TABLE IF NOT EXISTS articles (
    doc_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS article_metadata (
    doc_id TEXT PRIMARY KEY,
    core_problem TEXT NOT NULL,
    target_audience TEXT NOT NULL,
    solution_framework TEXT NOT NULL, -- JSON String
    topic_tags TEXT NOT NULL,         -- JSON String
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id)
);

-- 검색용 FTS5 가상 테이블
CREATE VIRTUAL TABLE IF NOT EXISTS metadata_fts USING fts5(
    doc_id UNINDEXED,
    core_problem,
    target_audience,
    solution_framework,
    topic_tags,
    tokenize = 'porter unicode61'
);

```

---

## 5. 기술 스택 및 환경 제약

* **언어 및 런타임**: Python 3.11 이상
* **주요 라이브러리**:
* 데이터 제어: `pydantic>=2.0`
* 데이터베이스: Python 표준 라이브러리 `sqlite3` (FTS5 활성화 필수)
* 비동기 처리: `asyncio`, `aiofiles`
* LLM 인터페이스: LiteLLM 또는 Provider 표준 SDK (OpenAI/Anthropic 호환 인터페이스로 구현하여 모델 교체 용이성 확보)
* CLI 구축: `typer` 또는 `argparse`


* **하드웨어 및 인프라 제약**:
* 벡터 DB(Milvus, Qdrant, Chroma 등) 데몬 프로세스 구동 불가 (로컬 메모리 절약).
* 임베딩 모델 로컬 로드 배제 (CPU/RAM 점유 방지).
* 모든 연산은 파일 기반 SQLite 및 외부 경량 API 호출로만 처리.



---

## 6. 개발 검증 및 완료 기준 (Definition of Done)

1. **배치 안정성**: 4,000편 추출 과정 중 네트워크 단절이나 API 타임아웃 발생 시, 기수행된 데이터를 보존하고 즉시 이어받기 구동이 가능한가.
2. **무손실 검색**: 입력된 주제 키워드에 대해 FTS5 기반으로 100ms 이내에 상위 2~3편의 후보 아티클 ID가 추출되는가.
3. **파이프라인 결합도**: CLI 단일 명령어로 [주제 입력 $\rightarrow$ 2편 원문 추출 $\rightarrow$ LLM 롱컨텍스트 주입 $\rightarrow$ 융합 초안 마크다운 생성]이 한 번에 완료되는가.
4. **코드 품질**: 외부 모듈 교체(LLM Provider 변경 등)가 가능하도록 추출기, 저장소, 생성기 클래스가 명확히 인터페이스로 분리되어 있는가.