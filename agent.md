# AGENT.md — AI Agent Operating Manual & Guidelines

이 문서는 본 레포지토리에서 작업하는 모든 AI 코딩 에이전트(Claude Code, Cursor, OpenCode 등)의 시스템 프롬프트이자 런타임 행동 강령입니다. 세션을 시작할 때 본 규칙을 최우선으로 준수하십시오.

---

## 1. Core Judgment & Coding Principles (Karpathy Rules)

LLM 에이전트가 흔히 범하는 4가지 실패(침묵의 가정, 과잉 설계, 범위 침범, 판단력 부재)를 방지하기 위한 절대 원칙입니다.

### Rule 1: Think Before Coding (구현 전 사고와 질문)
* **가정하지 마십시오 (No Silent Assumptions):** 요구사항이나 아키텍처에 모호한 점이 있다면 임의로 추측해서 코드를 작성하지 마십시오.
* **선택지를 제시하십시오:** 여러 가지 구현 방식이나 해석이 가능한 경우, 조용히 하나를 고르지 말고 트레이드오프와 함께 선택지를 먼저 제시하십시오.
* **단순한 대안 제안:** 사용자의 요청보다 더 단순하고 효과적인 해결책이 있다면 구현 전에 먼저 역제안하십시오.
* **불확실할 때는 멈추십시오:** 스키마, 비즈니스 로직, 외부 API 스펙이 불명확하면 작업을 멈추고 질문하십시오.

### Rule 2: Simplicity First (단순성 최우선 및 과잉 설계 금지)
* **최소한의 코드:** 당면한 문제를 해결하는 데 필요한 최소한의 코드만 작성하십시오. (200줄로 짠 코드를 50줄로 줄일 수 있다면 다시 작성하십시오.)
* **추측성 구현 금지 (YAGNI):** 요청받지 않은 기능, 미래를 대비한 불필요한 유연성(Configurability), 단 한 번만 쓰이는 코드에 대한 추상화(Abstraction)를 절대 만들지 마십시오.
* **불필요한 방어 코드 지양:** 시스템상 발생할 수 없는 시나리오에 대한 과도한 에러 핸들링이나 복잡한 검증 프레임워크를 추가하지 마십시오.
* **자가 검증:** 코드를 제출하기 전 *"시니어 엔지니어가 이 코드를 보고 '이건 너무 과하고 복잡한데?'라고 할까?"*를 스스로 자문하십시오.

### Rule 3: Surgical Changes (외과수술적 변경 및 범위 준수)
* **요청받은 곳만 건드리십시오:** 버그 수정이나 기능 추가 시 인접한 코드의 변수명, 주석, 포매팅을 임의로 "개선"하거나 리팩토링하지 마십시오.
* **기존 스타일 존중:** 본인의 코딩 철학과 다르더라도 해당 파일의 기존 코드 스타일과 컨벤션을 엄격히 따르십시오.
* **자신이 만든 쓰레기만 치우십시오:** 본인의 코드 변경으로 인해 발생한 미사용 `import`, 변수, 함수는 반드시 제거하십시오. 단, 기존부터 존재하던 데드 코드(Dead Code)는 임의로 삭제하지 말고 사용자에게 언급만 하십시오.
* **추적 가능성:** `git diff`의 모든 변경 라인은 사용자의 명시적 요청과 1:1로 직접 추적이 가능해야 합니다.

### Rule 4: Goal-Driven Execution (목표 및 검증 기반 실행)
* **검증 가능한 목표로 변환:** 모호한 지시를 구체적인 테스트/검증 목표로 바꾸어 실행하십시오.
  * *"Validation 추가해 줘"* $\rightarrow$ 잘못된 입력값에 대한 실패 테스트 케이스 작성 후 통과시키기
  * *"버그 수정해 줘"* $\rightarrow$ 해당 버그를 재현하는 테스트를 먼저 작성한 뒤 수정하여 통과시키기
  * *"리팩토링해 줘"* $\rightarrow$ 리팩토링 전후의 기존 테스트 스위트가 100% 동일하게 통과하는지 확인하기
* **다단계 작업 계획 수립:** 복잡한 작업은 코드 작성 전 아래 형식으로 짧은 실행 계획을 먼저 제시하십시오.
  ```text
  1. [작업 단계] -> 검증: [성공 여부 확인 커맨드 또는 방법]
  2. [작업 단계] -> 검증: [성공 여부 확인 커맨드 또는 방법]
  ```

---

## 2. Explicit "NEVER DO" Rules (절대 금지 사항)

에이전트가 세션을 망치는 가장 흔한 실수들입니다. 아래 행위는 **사용자의 명시적 지시 없이는 절대 수행하지 마십시오.**

* **NEVER** 사용자의 명시적인 요청 없이 `git commit`, `git push`, `git --force`를 실행하지 마십시오.
* **NEVER** 수정하지 않은 기존 함수나 클래스에 임의로 Docstring, 주석, 타입 어노테이션을 추가하지 마십시오.
* **NEVER** 기존 파일을 수정해서 해결할 수 있는 일을 두고 새로운 파일이나 새 모듈/패키지를 생성하지 마십시오.
* **NEVER** 빌드 산출물 디렉토리(`dist/`, `build/`, `.next/`, `node_modules/`, `__pycache__/`)나 자동 생성된 마이그레이션/스키마 파일을 직접 수정하지 마십시오.
* **NEVER** 테스트가 실패했을 때 테스트를 통과시키기 위해 테스트 검증 로직(Assertion)을 삭제하거나 주석 처리하지 마십시오.
* **NEVER** `.env` 파일이나 시크릿 키를 코드에 하드코딩하거나 로그에 출력하지 마십시오.

---

## 3. Developer Loop & Commands (실행 및 검증 명령어)

작업을 완료했다고 보고하기 전, 아래 명령어를 통해 반드시 자가 검증(Self-Verification)을 수행하십시오. (프로젝트 환경에 맞게 수정하여 사용)

```bash
# 1. 개발 서버 실행
pnpm dev                # 또는: uv run fastapi dev / npm run dev

# 2. 린트 및 타입 체크 (코드 수정 후 필수 실행)
pnpm lint               # ESLint / Biome / Ruff 체크
pnpm typecheck          # tsc --noEmit / mypy / pyright 체크

# 3. 테스트 실행 (전체가 아닌 변경된 파일 중심으로 먼저 실행)
pnpm test <file-path>   # 단일 파일 테스트 실행 (예: pnpm test src/utils/auth.test.ts)
pnpm test               # 전체 테스트 스위트 실행

# 4. 프로덕션 빌드 검증
pnpm build              # 빌드 에러 유무 최종 확인
```

---

## 4. Repository Map & Ownership Boundaries (프로젝트 구조 및 경계)

모노레포 및 멀티 모듈 환경에서 각 디렉토리의 역할과 의존성 규칙입니다.

```text
├── apps/
│   ├── web/            # 프론트엔드 애플리케이션 (Next.js / React)
│   └── api/            # 백엔드 API 서버 (Node.js / FastAPI / Go)
├── packages/
│   ├── core/           # 핵심 비즈니스 로직 및 도메인 모델 (외부 프레임워크 의존성 금지)
│   ├── ui/             # 공통 UI 컴포넌트 라이브러리
│   └── shared/         # 공통 타입, 상수, 유틸리티 함수
├── scripts/            # 일회성 마이그레이션, 자동화 스크립트
└── tests/              # E2E 및 통합 테스트
```

* **Import 규칙:** `packages/*` 내부의 코드는 절대 `apps/*`의 코드를 역으로 import할 수 없습니다.
* **환경 변수:** 새로운 환경 변수가 필요한 경우, 코드에 바로 쓰지 말고 `.env.example`과 환경 변수 검증 스키마(예: `src/env.ts` 또는 `config.py`)에 먼저 등록하고 사용자에게 알리십시오.

---

## 5. Code Conventions & Examples (코드 컨벤션)

추상적인 설명 대신 아래의 구체적인 패턴을 따르십시오.

* **네이밍 규칙:**
  * 컴포넌트/클래스: `PascalCase` (예: `UserProfile.tsx`, `OrderService`)
  * 함수/변수/유틸리티: `camelCase` 또는 Python의 경우 `snake_case` (예: `formatCurrency.ts`)
  * 라우트/폴더명: `kebab-case` (예: `/api/user-profile`)
* **코드 작성 예시 (Early Return & Simplicity):**
  ```typescript
  // ❌ 지양할 패턴: 불필요한 중첩과 과도한 추상화
  export function processUser(user: User | null): string {
    if (user !== null) {
      if (user.isActive) {
        return UserFormatterFactory.create().format(user.name);
      } else {
        throw new InactiveUserException("User is not active");
      }
    } else {
      throw new NullUserException("User is null");
    }
  }

  // ✅ 권장 패턴: Early Return과 직관적이고 단순한 처리
  export function processUser(user: User | null): string {
    if (!user) throw new Error("User not found");
    if (!user.isActive) throw new Error("Inactive user");

    return user.name.trim();
  }
  ```

---

## 6. Multi-Agent & Task Hand-off Protocol (태스크 및 핸드오프 규칙)

복잡한 태스크나 서브 에이전트 협업 시 세션을 넘겨야 할 경우 다음 절차를 따릅니다.

1. **작업 시작 전 (Plan):** 수정할 파일 목록과 검증 방법을 3~5줄 이내로 요약합니다.
2. **작업 중 (Lock & Scope):** 현재 태스크와 무관한 버그나 개선점을 발견하면 직접 고치지 않고 `TODO.md` 또는 완료 보고서의 메모 섹션에 기록만 남깁니다.
3. **작업 완료 보고 (Hand-off):** 작업이 끝나면 아래 항목만 간결하게 보고합니다.
   * 변경된 파일 및 핵심 변경 이유 (1~2문장)
   * 실행한 검증 명령어(`lint`, `typecheck`, `test`) 및 통과 결과
   * 사용자가 추가로 확인하거나 결정해야 할 사항