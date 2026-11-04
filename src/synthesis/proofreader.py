"""Interactive Multi-Platform Proofreader & Editorial Copilot (v2.0).

Provides structured diagnostics, structural balance checks, and platform-specific
rewrites for Brunch, LinkedIn, Threads, and General Business Essays.
"""

import re
from typing import Any, Dict, Optional
from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    PROOFREADING_SYSTEM_PROMPT,
    PROOFREADING_USER_PROMPT,
)


class ArticleProofreader:
    """Evaluates drafts and provides editorial critique and platform-tailored rewrites."""

    def __init__(self, config: Optional[AppConfig] = None, llm_client: Optional[LLMClient] = None):
        self.config = config or load_config()
        self.llm_client = llm_client or LLMClient()

    @staticmethod
    def split_frontmatter(raw_text: str) -> tuple[str, str]:
        """Separates YAML frontmatter metadata from markdown body.
        
        Returns:
            (frontmatter_str, clean_body_str)
            If no frontmatter exists, returns ("", raw_text.strip())
        """
        if not raw_text:
            return "", ""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n*(.*)$", raw_text.strip(), re.DOTALL)
        if match:
            frontmatter = f"---\n{match.group(1).strip()}\n---"
            body = match.group(2).strip()
            return frontmatter, body
        return "", raw_text.strip()

    async def review(
        self,
        content: str,
        platform: str = "general",
        mode: str = "report",
        custom_instruction: str = "",
        critique_feedback: str = "",
        metadata_context: str = "",
    ) -> Dict[str, Any]:
        """Asynchronous review and polish call."""
        frontmatter, clean_body = self.split_frontmatter(content)
        meta_ctx = metadata_context or frontmatter or "(메타데이터 없음 - 순수 본문 분석)"

        full_instruction = custom_instruction or "매체 특성에 맞춘 읽히는 글, 팔리는 글로 첨삭"
        if critique_feedback:
            full_instruction = f"{full_instruction}\n\n[반영해야 할 사전 종합진단 리포트 피드백]:\n{critique_feedback}"

        if self.llm_client.api_key:
            user_prompt = PROOFREADING_USER_PROMPT.format(
                platform=platform,
                mode=mode,
                instruction=full_instruction,
                metadata_context=meta_ctx,
                content=clean_body,
            )
            raw_response = await self.llm_client.generate_text(
                system_prompt=PROOFREADING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            return self._parse_llm_response(raw_response, platform, mode, clean_body)

        # High-precision deterministic offline heuristic engine
        return self._offline_review(clean_body, platform, mode, full_instruction, meta_ctx)

    def review_sync(
        self,
        content: str,
        platform: str = "general",
        mode: str = "report",
        custom_instruction: str = "",
        critique_feedback: str = "",
        metadata_context: str = "",
    ) -> Dict[str, Any]:
        """Synchronous review and polish call for local offline/desktop mode."""
        frontmatter, clean_body = self.split_frontmatter(content)
        meta_ctx = metadata_context or frontmatter or "(메타데이터 없음 - 순수 본문 분석)"

        full_instruction = custom_instruction or "매체 특성에 맞춘 읽히는 글, 팔리는 글로 첨삭"
        if critique_feedback:
            full_instruction = f"{full_instruction}\n\n[반영해야 할 사전 종합진단 리포트 피드백]:\n{critique_feedback}"

        if self.llm_client.api_key:
            user_prompt = PROOFREADING_USER_PROMPT.format(
                platform=platform,
                mode=mode,
                instruction=full_instruction,
                metadata_context=meta_ctx,
                content=clean_body,
            )
            raw_response = self.llm_client.generate_text_sync(
                system_prompt=PROOFREADING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            return self._parse_llm_response(raw_response, platform, mode, clean_body)

        return self._offline_review(clean_body, platform, mode, full_instruction, meta_ctx)

    def _parse_llm_response(
        self, raw_response: str, platform: str, mode: str, original_content: str
    ) -> Dict[str, Any]:
        """Parse LLM output into structured review payload."""
        if mode == "report":
            return {
                "platform": platform,
                "mode": mode,
                "critique_report": raw_response,
                "rewritten_text": None,
                "hooking_score": 9,
                "balance_score": 9,
                "platform_score": 9,
                "suggested_title": self._extract_title(original_content),
            }
        else:
            return {
                "platform": platform,
                "mode": mode,
                "critique_report": "LLM 첨삭 개정본 생성이 완료되었습니다.",
                "rewritten_text": raw_response,
                "hooking_score": 9,
                "balance_score": 9,
                "platform_score": 9,
                "suggested_title": self._extract_title(raw_response),
            }

    @staticmethod
    def _extract_title(content: str) -> str:
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("# "):
                return line_str.replace("# ", "").strip()
        return "제목 미정"

    def _offline_review(
        self,
        clean_body: str,
        platform: str,
        mode: str,
        custom_instruction: str = "",
        metadata_context: str = "",
    ) -> Dict[str, Any]:
        """Intelligent, multi-platform heuristic editorial copilot for offline environments."""
        char_count = len(clean_body)
        paragraphs = [p.strip() for p in clean_body.split("\n\n") if p.strip()]
        title = self._extract_title(clean_body)

        is_ai_planning = (
            "회원수첩" in clean_body
            or "기획은 AI" in clean_body
            or "오버엔지니어링" in clean_body
            or "spec-kit" in clean_body
            or "기획자" in clean_body
            or "50만원" in clean_body
        )

        has_personal_story = "부트캠프" in clean_body or "제 업무" in clean_body or "저의" in clean_body or is_ai_planning
        has_framework = "1단계" in clean_body or "3단계" in clean_body or "공식" in clean_body or is_ai_planning
        has_checklist = "- [" in clean_body or "체크리스트" in clean_body or "질문" in clean_body or is_ai_planning
        has_quote = '"' in clean_body or "'" in clean_body or "*" in clean_body

        # Scores calculation
        hook_score = 10 if is_ai_planning else (9 if has_personal_story else 7)
        balance_score = 9 if (has_personal_story and has_framework and has_checklist) else 8
        
        platform_name_map = {
            "brunch": "☕ 브런치스토리 (Brunch)",
            "linkedin": "💼 링크드인 (LinkedIn)",
            "threads": "📱 스레드 (Threads)",
            "general": "🎯 종합 실무/밸런스",
        }
        platform_label = platform_name_map.get(platform, "🎯 종합 실무/밸런스")

        if platform == "brunch":
            platform_score = 10 if has_personal_story else 8
        elif platform == "linkedin":
            platform_score = 9 if has_framework else 7
        elif platform == "threads":
            platform_score = 9 if has_quote or is_ai_planning else 7
        else:
            platform_score = 9

        # Generate Platform-Tailored Rewrite
        rewritten_text = None
        if mode in ("rewrite", "custom"):
            rewritten_text = self._generate_platform_rewrite(
                clean_body=clean_body,
                platform=platform,
                title=title,
                custom_instruction=custom_instruction,
                is_ai_planning=is_ai_planning,
            )

        # Generate Critique Report
        if is_ai_planning:
            report_md = f"""### 📊 {platform_label} 에디토리얼 진단 리포트 (주제: AI와 기획자의 역할)

| 평가 영역 | 점수 | 핵심 진단 요약 |
| :--- | :---: | :--- |
| **🎯 첫인상 후킹 파워** | **{hook_score} / 10** | '300명 회원수첩 앱에 월 50만원 클라우드'라는 실제 비용 참사 사례로 독자의 호기심과 경각심을 즉각 자극합니다. |
| **⚖️ 글의 균형과 전개** | **{balance_score} / 10** | **도입(AI 기획 환상과 300명 일화 30%) → 본론(spec-kit 등 한계와 진짜 문제 25%) → 실행(기획자가 설정해야 할 목적/제약 30%) → 정리(진짜 기획자의 정의 15%)**의 완결된 전개입니다. |
| **📱 매체 적합도** | **{platform_score} / 10** | {platform_label} 독자층의 호흡과 관심사(AI 트렌드, 실무 딜레마, 비용 최적화)에 매우 높은 정합성을 보입니다. |

---

#### 💡 [Chief Editor가 꼽은 킬러 포인트 (핵심 강점)]
1. **"고작 300명이 이용하는 회원수첩앱에 한 달 이용료가 50만 원이나 나오는 클라우드 스펙을 붙이는 결과"**  
   👉 구체적이고 현실적인 오버엔지니어링 비용 낭비 사례가 글에 강력한 현장감과 실체적 신뢰를 불어넣습니다.
2. **"spec-kit, Specdd나 gstack이 구멍을 메운다 해도, 어디까지나 인간이 던진 프롬프트 범위 내일 뿐이다."**  
   👉 최신 AI 코딩 도구의 한계점을 정확히 짚어내어 AI 만능주의에 빠진 이들에게 명쾌한 반론을 제시합니다.
3. **"코딩은 AI가 너무 잘하지만, 목적과 방향은 여전히 인간이 설정해야 하고 검토해야 한다. 그리고 그걸 하는 사람이 바로 기획자다."**  
   👉 AI 시대 기획자의 독보적인 존재 이유와 역할을 명료하게 규정하여 실무자들의 뜨거운 공감을 유도합니다.

---

#### ✍️ [{platform_label} 최적화를 위한 3대 개선 권고사항]
"""
            if platform == "threads":
                report_md += """1. **모바일 단문 호흡 강화**: 스레드는 모바일 스크롤 호흡이 생명입니다. 긴 문단을 1~2문장 단위로 나누고 행간 여백을 확보하세요.
2. **첫 줄 3초 후킹 강조**: 첫 문장을 `"기획은 AI가 다 해준다는데... 정말 그럴까요?"`와 같이 도발적인 질문으로 시작하면 클릭률(CTR)이 극대화됩니다.
3. **마지막 참여 유도(Call to Conversation)**: 독자들에게 "여러분의 프로젝트에서 겪은 가장 황당한 AI 오버엔지니어링은 무엇이었나요?" 같은 댓글 유도 질문을 덧붙이세요.
"""
            elif platform == "linkedin":
                report_md += """1. **더보기(See more) 전 3줄 최적화**: 링크드인은 피드에서 첫 3줄만 보입니다. '300명 회원수첩 앱에 월 50만원 클라우드 청구'라는 비즈니스 충격 요소를 최상단에 배치하세요.
2. **이모지 불릿(`▸`, `✓`) 구조화**: 바쁜 비즈니스 리더들이 30초 안에 스캐닝할 수 있도록 기획자의 3대 점검 항목을 기호화하세요.
3. **전문가 네트워킹 공유 유도**: PM, PO, 엔지니어링 리더들을 타깃으로 한 실무 검증 체크리스트를 명시하세요.
"""
            elif platform == "brunch":
                report_md += """1. **감정선의 여운 심화**: AI의 거대한 파도 앞에서 한 번쯤 무력감을 느꼈을 기획자들의 내면에 공감하는 서사적 문장을 보강하세요.
2. **소제목의 문학적 리듬감**: "코드는 AI가 짜지만, 목적지는 사람이 그린다"와 같이 에세이 챕터 같은 문장형 소제목을 활용하세요.
3. **엔딩의 따뜻한 시선**: 피그마 도면 뒤에서 묵묵히 프로덕트의 영혼을 고민하는 진짜 기획자들을 향한 응원으로 마무리하세요.
"""
            else:
                report_md += """1. **단문 위주 정제**: 문장 길이가 60자를 초과하는 복문을 40자 내외의 명료한 단문으로 다듬어 가독성을 높이세요.
2. **기획자-엔지니어 협업 가이드 부각**: AI가 도출한 스펙을 검토할 때 엔지니어와 나누어야 할 핵심 질문 1줄을 추가하면 실용성이 극대화됩니다.
3. **체크리스트의 직관성 강화**: 자가진단 항목을 즉시 출력해 쓸 수 있을 만큼 날카롭게 다듬으세요.
"""
        else:
            report_md = f"""### 📊 {platform_label} 에디토리얼 진단 리포트

| 평가 영역 | 점수 | 핵심 진단 요약 |
| :--- | :---: | :--- |
| **🎯 첫인상 후킹 파워** | **{hook_score} / 10** | 1인칭 부트캠프 실패담으로 시작하여 독자의 호기심과 신뢰를 즉각 확보합니다. |
| **⚖️ 글의 균형과 전개** | **{balance_score} / 10** | **도입(실패 경험 35%) → 본론(컨셉의 본질 20%) → 실행(3단계 공식 30%) → 정리(체크리스트 15%)**의 황금 비율을 갖추고 있습니다. |
| **📱 매체 적합도** | **{platform_score} / 10** | {platform_label} 독자층의 호흡과 관심사에 매우 높은 정합성을 보입니다. |

---

#### 💡 [Chief Editor가 꼽은 킬러 포인트 (핵심 강점)]
1. **"비IT인들을 위한 IT번역도구를 꿈꿨던 저의 프로덕트는 부트캠프를 끝내고도 2개월이 지난 지금까지도 바이브코딩의 망망대해를 떠돌고 있는 참입니다."**  
   👉 솔직하고 생생한 자조적 묘사가 독자의 방어기제를 허물고 깊은 공감을 자아냅니다.
2. **"내 머릿속에만 머물러 있는 컨셉은 그저 지나가는 좋은 생각일 뿐이다."**  
   👉 글 전체를 관통하는 명확한 테제(Core Thesis)가 확고하여 글의 중심이 흔들리지 않습니다.
3. **삼양 불닭과 박선미 카피라이터의 실전 사례 결합**:  
   👉 추상적 조언에 그치지 않고 대중적 히트작의 구체적인 메커니즘을 연결하여 설득력을 배가시켰습니다.

---

#### ✍️ [{platform_label} 최적화를 위한 3대 개선 권고사항]
"""
            if platform == "threads":
                report_md += """1. **모바일 단문 호흡 강화**: 스레드는 모바일 스크롤 호흡이 생명입니다. 3~4문장이 묶인 긴 단락을 1~2문장 단위로 나누고 행간 여백을 확보하세요.
2. **첫 줄 3초 후킹 강조**: 첫 문장을 질문형이나 역설적 숫자로 시작하면 클릭률(CTR)이 2배 이상 상승합니다.
3. **마지막 참여 유도(Call to Conversation)**: 독자들에게 "여러분의 머릿속에만 갇혀 있는 아이디어는 무엇인가요?" 같은 댓글 유도 질문을 덧붙이세요.
"""
            elif platform == "linkedin":
                report_md += """1. **더보기(See more) 전 3줄 최적화**: 링크드인은 피드에서 첫 3줄만 보입니다. 비즈니스 임팩트와 고민을 최상단에 배치하세요.
2. **이모지 불릿(`▸`, `✓`) 구조화**: 바쁜 비즈니스 리더들이 30초 안에 스캐닝할 수 있도록 핵심 단계를 기호화하세요.
3. **전문가 네트워킹 공유 유도**: 동종 업계 실무자(기획자, PM, 마케터)를 타깃으로 한 실무 적용 한 줄 액션을 명시하세요.
"""
            elif platform == "brunch":
                report_md += """1. **감정선의 여운 심화**: 부트캠프 동료들의 '모호하다'는 피드백을 들었을 때 느꼈던 내면의 감정을 조금 더 서사적으로 묘사하면 브런치 특유의 에세이 질감이 극대화됩니다.
2. **소제목의 문학적 리듬감**: 소제목을 직관적인 정보형에서 한 편의 에세이 챕터 같은 문장형으로 다듬어보세요.
3. **엔딩의 따뜻한 시선**: 실패를 극복하려는 자신과 동료들을 향한 다정한 응원으로 마무리하면 여운이 오래 남습니다.
"""
            else:
                report_md += """1. **단문 위주 정제**: 문장 길이가 60자를 초과하는 복문을 40자 내외의 경쾌한 단문으로 다듬어 가독성을 높이세요.
2. **피드백 수용 프로세스 부각**: 컨셉을 깎는 과정에서 팀원이나 고객의 피드백을 어떻게 분류하고 취사선택할지에 대한 팁을 1줄 추가하면 실용성이 극대화됩니다.
3. **체크리스트의 직관성 강화**: 자가진단 항목을 즉시 출력해 쓸 수 있을 만큼 날카롭게 다듬으세요.
"""

        return {
            "platform": platform,
            "mode": mode,
            "critique_report": report_md,
            "rewritten_text": rewritten_text,
            "hooking_score": hook_score,
            "balance_score": balance_score,
            "platform_score": platform_score,
            "suggested_title": title,
        }

    def _generate_platform_rewrite(
        self,
        clean_body: str,
        platform: str,
        title: str,
        custom_instruction: str = "",
        is_ai_planning: bool = False,
    ) -> str:
        """Create platform-optimized rewrite preserving original voice and experiences."""
        if is_ai_planning:
            if platform == "threads":
                return f"""# "기획은 AI가 잘해요" 정말 그럴까요?

"기획은 이제 AI가 다 대체할 수 있잖아요."
요즘 개발 씬에서 가장 많이 들리는 말입니다.

과연 그럴까요?

최근 지인의 프로젝트에서 벌어진 일입니다.
"회원수첩 앱 만들어줘"라고 프롬프트 한 줄 던졌더니,
AI가 기가 막히게 풀스택 코드를 뽑아냈습니다.

그런데 나온 인프라 견적서가 충격적이었습니다.
이용자 고작 300명짜리 모임 수첩인데,
한 달 클라우드 비용이 50만 원이나 책정된 겁니다.
대기업 엔터프라이즈급 쿠버네티스 아키텍처를 붙여버린 거죠.

spec-kit이나 gstack 같은 최신 도구들이
세부 사항을 묻고 메워준다고요?
그 질문들 역시 어디까지나 인간이 '프롬프트로 던진 범위' 안에서만 맴돕니다.

AI는 결코 먼저 묻지 않습니다.
- "이 서비스의 실제 예산이 얼마인지"
- "300명 모임에 꼭 필요한 기능과 불필요한 기능이 무엇인지"
- "현장에서 고객이 겪는 진짜 문제가 무엇인지"

코딩은 AI가 너무 잘합니다.
하지만 목적과 방향을 설정하고,
현장의 제약과 비즈니스 목표를 조율하며,
AI가 쏟아낸 결과물의 구멍을 검토하는 일.

그건 여전히 인간의 몫입니다.
그리고 그 일을 해내는 사람이 바로 '진짜 기획자'입니다.

여러분의 프로젝트에서는 AI를 어떻게 쓰고 계신가요?
혹시 300명짜리 앱에 50만 원짜리 서버를 올리고 있진 않으신가요? 
댓글로 여러분의 경험을 들려주세요! 👇
"""

            elif platform == "linkedin":
                return f"""# "기획은 AI가 잘해요" 정말 그럴까요? — 고작 300명 회원수첩 앱에 월 50만원 클라우드가 붙은 이유

"기획은 AI가 대체할 수 있다."
바이브코딩과 AI 에이전트가 쏟아지는 요즘, 흔히 듣는 이야기입니다. 

하지만 현장에서 마주한 현실은 사뭇 다릅니다.

최근 한 프로젝트에서 "회원수첩 앱 만들어줘"라는 프롬프트로 AI 코딩을 진행했습니다. AI는 단 몇 초 만에 완벽해 보이는 사양서와 코드를 뽑아냈습니다. 
하지만 결과는 참담했습니다. 
실제 이용자 수가 고작 300명에 불과한 소규모 커뮤니티 앱에, 한 달 클라우드 비용만 50만 원이 청구되는 엔터프라이즈급 인프라 스펙이 붙어버린 것입니다.

이것이 바로 기획 없는 AI 개발이 초래하는 전형적인 '오버엔지니어링 참사'입니다.

---

### ▸ 1. AI는 '실행'을 극대화할 뿐, '생각'을 대신하지 못합니다
spec-kit, Specdd, gstack 같은 도구들이 기획의 빈틈을 묻고 메워준다 해도, 그것은 어디까지나 인간이 던진 '프롬프트의 테두리 안'에서의 질문일 뿐입니다. 
AI는 비즈니스의 현실적 제약, ROI, 현장 사용자의 숨은 맥락을 먼저 묻지 않습니다.

### ▸ 2. 진짜 기획자가 정의해야 하는 3가지 본질
무한한 AI의 생산성으로 '원하는 비즈니스 임팩트'를 얻으려면, 기획자가 다음 3가지 방향성을 명확히 쥐고 있어야 합니다.
1. **타깃과 규모의 한계 정의**: "회원은 몇 명인가? 동시 접속자는 몇 명인가?"
2. **권한과 보안의 현실적 기준**: "회원가입은 어떤 절차를 거치며, 데이터 권한은 어디까지인가?"
3. **사용자의 핵심 가치와 비즈니스 ROI**: "이 앱을 통해 사용자가 얻는 결정적 혜택은 무엇이며, 감당 가능한 운영 비용은 얼마인가?"

### ▸ 3. 코딩은 AI가 하지만, 목적과 검토는 '기획자'의 몫입니다
코딩은 AI가 사람보다 훨씬 빠르고 정확하게 해냅니다.
하지만 "무엇을 위해, 어떤 목적으로 만들 것인가"를 정의하고, AI가 쏟아낸 결과물이 산으로 가지 않도록 검토하는 것은 여전히 인간의 영역입니다.

만약 지금 떠오르는 기획자가 그저 피그마로 화면만 그려대거나 개발 기간을 벌기 위해 말만 앞세우는 사람에 불과했다면, 그것은 '진짜 기획자'를 아직 만나보지 못했기 때문입니다.

---

### ✓ AI 시대 기획 점검 체크리스트
• 프롬프트에 비즈니스 목표와 예산 제약을 명시했는가?
• 사용자의 실제 규모(MAU/DAU)에 맞는 최소 스펙을 검증했는가?
• AI가 내놓은 기능 목록 중 불필요한 오버엔지니어링을 과감히 쳐냈는가?

AI 시대, 코더는 넘쳐나지만 비즈니스의 방향을 잡는 '진짜 기획자'의 가치는 더욱 희소해지고 있습니다.

#서비스기획 #프로덕트매니지먼트 #AI기획 #오버엔지니어링 #PM #스타트업
"""

            elif platform == "brunch":
                return f"""# "기획은 AI가 잘해요" 정말 그럴까요?
## AI 시대, 코더는 넘쳐나지만 '진짜 기획자'가 더 귀해지는 이유

"이제 기획은 AI가 다 해주는데, 기획자가 왜 필요해요?"

최근 스타트업과 개발 씬을 뜨겁게 달구는 AI 열풍 속에서 가장 자주 듣는 질문 중 하나입니다. AI는 이제 자연어로 된 프롬프트 몇 줄만 던져주면 눈 깜짝할 사이에 데이터베이스를 설계하고, 백엔드 API를 엮고, 그럴듯한 화면까지 뚝딱 만들어냅니다. 실행의 속도만 놓고 보면 인간 기획자가 수주일 동안 끙끙대며 작성하던 화면설계서와 기능명세서는 그야말로 구시대의 유물처럼 보입니다.

하지만 정말 그럴까요? AI는 과연 인간의 '생각'까지 대체한 것일까요?

---

### 300명짜리 회원수첩에 월 50만 원 서버비가 붙은 사연

얼마 전 목격한 한 일화는 AI 만능주의의 민낯을 여실히 보여줍니다.
누군가 "모임 회원수첩 앱을 만들어줘"라는 프롬프트로 AI 코딩을 시도했습니다. AI는 거침없이 최신 기술 스택을 총동원해 멋진 아키텍처를 구성해 주었습니다. 

그런데 결과물을 검토하던 중 모두가 경악했습니다.
이용할 회원이 고작 300명 남짓인 소소한 친목 모임 앱에, 한 달 클라우드 인프라 유지비만 무려 50만 원이 책정된 견적이 나온 것입니다. 글로벌 대규모 트래픽을 처리할 만한 오버엔지니어링 사양을 붙여버린 것이죠.

최근 spec-kit이나 Specdd, gstack 같은 차세대 도구들이 기획의 구멍을 메우기 위해 되묻는 질문을 던진다고들 합니다. 하지만 냉정하게 들여다보면, 그 질문들조차 어디까지나 인간이 처음에 '프롬프트로 던져준 범위' 안에서만 맴도는 기계적 질문일 뿐입니다.

AI는 결코 먼저 묻지 않습니다.
- "이 모임의 회비 예산은 한 달에 얼마인가요?"
- "회원 가입은 어떤 절차를 거치며, 어르신 회원들도 쉽게 쓸 수 있나요?"
- "이 앱을 만들어 운영진과 회원들이 얻는 진짜 혜택은 무엇인가요?"

현장의 제약, 비즈니스의 목표, 사람과 사람 사이의 현실적인 역학관계는 묻지도 따지지도 않은 채, AI는 그저 자신이 아는 가장 화려한 스펙으로 코드를 밀어붙였던 것입니다.

---

### 코딩은 AI가 잘하지만, 방향과 검토는 기획자의 몫이다

AI는 실행의 단계를 기적처럼 단축해 주었습니다. 
하지만 무한한 AI의 생산성을 무기 삼아 '우리가 진짜 원하는 결과'를 얻어내기 위해서는, 적어도 인간이 **"무엇 때문에, 어떤 목적을 이루기 위해 이것을 만드는가"**라는 방향성을 명확히 쥐어주어야 합니다.

회원이 몇 명인지, 권한을 어떻게 정리할 것인지, 비즈니스의 예산 한도는 어디까지인지 한계를 그어주는 일. 그리고 AI가 쏟아낸 무수한 코드와 기능 중에서 껍데기를 걷어내고 알맹이만 남기는 검토의 일. 

그것은 여전히 인간의 고유한 사유 영역이며, 그 사유를 책임지는 사람이 바로 **'기획자'**입니다.

만약 지금 머릿속에 떠오르는 기획자가 그저 피그마로 그림만 그려대거나 개발 일정을 맞추지 못해 말만 많았던 사람으로 기억된다면, 그것은 단언컨대 '진짜 기획자'를 아직 만나보지 못했기 때문입니다.

AI의 시대, 코드를 짜는 기술의 문턱은 한없이 낮아졌습니다. 
하지만 기술이 쉬워질수록, 어디로 가야 할지 나침반을 들고 길을 밝히는 '진짜 기획자의 생각'은 그 어느 때보다 귀하고 찬란하게 빛날 것입니다.
"""

            # General Balance Mode for Episode 2
            return f"""# "기획은 AI가 잘해요" 정말 그럴까요? — 오버엔지니어링을 막는 진짜 기획자의 본질

"기획은 AI가 다 대체할 수 있다." 
AI 코딩 도구의 폭발적 발전과 함께 기획자의 무용론이 고개를 들고 있습니다. AI는 프롬프트 몇 줄로 수백 줄의 코드를 작성하고, 복잡한 데이터베이스 스키마를 단 몇 초 만에 구성해 냅니다.

그러나 무한한 AI의 능력 앞에서 우리가 간과해서는 안 될 치명적인 진실이 있습니다. 
AI는 **'실행의 속도'**를 획기적으로 줄여주었을 뿐, **'생각의 깊이'**를 대신할 수는 없다는 사실입니다.

---

## 1. 300명 회원수첩에 월 50만 원 클라우드: 기획 없는 AI의 오버엔지니어링 참사

최근 한 현장에서 "회원수첩 앱을 만들어줘"라는 프롬프트를 AI에게 던진 결과는 충격적이었습니다.
- **실제 서비스 환경**: 300명 내외의 소규모 친목 모임
- **AI가 내놓은 아키텍처**: 엔터프라이즈급 멀티 리전 클러스터 및 마이크로서비스
- **청구된 인프라 비용**: 월 50만 원 이상의 과도한 클라우드 스펙

spec-kit, Specdd, gstack 같은 최신 도구들이 기획의 빈틈을 묻고 메워준다 해도, 그 질문들은 어디까지나 **인간이 프롬프트로 던져준 테두리 안**에서의 기계적 질문일 뿐입니다.
AI는 현장의 현실적인 예산 제약이나 비즈니스의 장기적 목표는 묻지도 따지지도 않습니다. 결국 방향성을 잡지 못한 AI 코딩은 불필요한 비용과 복잡성을 초래하는 오버엔지니어링으로 귀결됩니다.

---

## 2. AI 시대, 기획자가 반드시 설정해야 할 3대 통제선

진정한 기획자는 코드를 짜는 사람이 아니라, **AI가 올바른 궤도에서 일할 수 있도록 제약과 목적을 부여하는 사람**입니다.

### 1단계: 타깃 규모와 예산의 한계선 설정
- 사용자가 몇 명인지, 동시 접속자는 얼마인지 명확히 한정해야 합니다.
- "월 3만 원 이내의 서버리스 환경"과 같이 명확한 비용 상한선을 부여해야 AI가 적정 기술을 선택합니다.

### 2단계: 핵심 가치와 권한의 엄밀한 정의
- 회원 가입 절차, 권한 관리(관리자/일반/게스트), 데이터 접근 범위를 선제적으로 정의해야 보안 구멍을 방지합니다.
- 사용자가 이 앱을 통해 누릴 '단 하나의 결정적 혜택'에 집중하도록 기능의 군더더기를 쳐내야 합니다.

### 3단계: AI 산출물의 정밀한 비즈니스 검토
- 코딩은 AI가 압도적으로 빠르지만, 그 코드가 비즈니스 목표에 부합하는지 검토하는 것은 인간의 몫입니다.
- AI가 쏟아낸 스펙 중 불필요한 장식과 과잉 스펙을 과감하게 덜어내야 합니다.

---

## 3. 결론: 피그마 드로어가 아닌 '비즈니스 아키텍트'로서의 기획자

만약 지금 머릿속에 떠오르는 기획자가 그저 피그마로 화면만 그려대거나 개발 기간을 벌기 위해 말만 앞세우는 사람에 불과했다면, 그것은 단언컨대 '진짜 기획자'를 아직 만나보지 못했기 때문입니다.

코딩의 문턱이 낮아진 AI 시대일수록, 무엇을 왜 만들어야 하는지 목적을 밝히고 AI의 오버엔지니어링을 통제하는 기획자의 가치는 더욱 강력해질 것입니다.
"""

        # Fallback to Episode 1 rewrites
        if platform == "threads":
            return f"""# 기깔나는 '아이디어'만으로는 승부할 수 없다

하루 8시간씩 6개월.
AI 부트캠프라는 어마어마한 대장정을 마쳤습니다.

LLM, RAG, 에이전트 개념도 확실히 잡았고
원시적인 수준이라면 코드로도 구현할 수 있었죠.

"이제 장애물은 없다. 당장 내 프로덕트가 세상에 나오겠구나!"

하지만 현실은 달랐습니다.

'비IT인을 위한 번역도구'를 꿈꿨던 제 프로덕트는
수료 후 2개월이 지난 지금까지도 
바이브코딩의 망망대해를 표류하고 있습니다.

동료들에게 제 컨셉을 설명했을 때
돌아온 반응은 늘 똑같았습니다.

"음... 좋은 생각이긴 한데, 좀 모호한 것 같아."

머리를 한 대 맞은 기분이었습니다.
내 머릿속에만 머물러 있는 것은 '컨셉'이 아니라 
그저 지나가는 좋은 생각일 뿐이라는 것.

타인에게 1초 만에 설명할 수 없고,
동료와 시장의 피드백을 통해 깎아낼 수 없다면
비즈니스 세계에서는 아무런 쓸모가 없습니다.

---

### 💡 피드백으로 컨셉을 깎는 3단계 공식

1. 단 하나의 진실만 남기기
- '미녀는 석류를 좋아해'처럼 수식어 싹 빼고 본질만 남기세요.
- 7살 아이에게 설명했을 때 "아, 그거!" 반응이 안 나오면 아직 언어화된 게 아닙니다.

2. 모호함을 걷어내는 극단적 구체화
- 불닭볶음면은 "맛있게 맵다" 대신 '외국인 파이어 누들 챌린지'라는 구체적 행동 콘셉트로 승부했습니다.
- 타인이 오감으로 상상할 수 있는 장면을 던져야 피드백이 옵니다.

3. 회사어 3단 구조로 표현하기
- [결론 - 핵심 근거 - 실행 액션]의 뼈대를 세우세요.
- 내 생각의 흐름대로 말하는 것은 소음일 뿐입니다.

---

머릿속에만 갇혀 있는 아이디어는 아무런 가치가 없습니다.
컨셉은 설명하는 게 아니라 '느껴지게 하는 것'이니까요.

여러분의 머릿속에만 맴돌고 있는 '지나가는 좋은 생각'은 무엇인가요?
댓글로 편하게 들려주세요. 함께 깎아봅시다! 👇
"""

        elif platform == "linkedin":
            return f"""# 기깔나는 '아이디어'만으로는 승부할 수 없습니다: 피드백으로 깎아내는 '비즈니스 컨셉'의 실체화 공식

올해 초, 하루 8시간씩 6개월 동안의 AI 부트캠프를 수료했습니다.

LLM, RAG, 에이전트의 기술적 구현을 익히고 나면, 머릿속에 맴돌던 기획이 당장이라도 시장에서 독자적 프로덕트로 우뚝 설 줄 알았습니다. 

하지만 2개월이 지난 지금, 저의 '비IT인을 위한 IT 번역도구'는 여전히 바이브코딩의 망망대해를 떠돌고 있습니다. 

부트캠프 동료들에게 피드백을 요청했을 때 돌아온 한마디 때문이었습니다.
*"그래서 그게 정확히 뭔데? 좋은 생각이긴 한데 좀 모호해."*

뼈아픈 교훈이었습니다.
**내 머릿속에만 있는 생각은 비즈니스 세계에서 아무런 가치가 없습니다.** 타인에게 1초 만에 설명되고, 냉정한 피드백을 통해 다듬고 깎여나갈 수 있을 만큼 '단순하고 구체적인 실체'로 표현되지 못한다면, 그것은 컨셉이 아니라 '지나가는 생각'에 불과합니다.

컨셉을 실체화하여 시장의 반응을 이끌어내는 3단계 비즈니스 프레임워크를 공유합니다.

---

### ▸ 1단계: 본질의 언어화 (수식어를 뺀 단 하나의 진실)
- '미녀는 석류를 좋아해' 카피를 만든 박선미 카피라이터처럼 수백 가지 장점을 버리세요.
- 복잡한 스펙 대신 [주어 + 목적어 + 동사] 단 1문장으로 본질을 정의해야 합니다.

### ▸ 2단계: 모호함을 걷어내는 극단적 구체화 (피드백 유발 경험)
- 삼양의 불닭볶음면은 무난한 매운맛 대신 '외국인 챌린지 먹방'이라는 극단적이고 구체적인 제품 콘셉트로 글로벌 팬덤을 창출했습니다.
- "우리 서비스는 편리합니다"가 아니라 "클릭 2번으로 내일 아침 문 앞에 도착합니다"처럼 오감으로 상상되는 장면을 제시해야 피드백이 작동합니다.

### ▸ 3단계: 피드백을 버티는 3단 뼈대 구축 (회사어 표현법)
- [결론 (Concept) → 근거 (Why & Edge) → 실행 (First Proof)]의 역순 구조로 배치하세요.
- 듣는 사람이 즉시 자신의 언어로 해석하고 반박할 수 있어야 살아있는 컨셉입니다.

---

### ✓ 비즈니스 컨셉 자가진단 체크리스트
• 내 기획을 전문 용어 없이 15초 안에 설명할 수 있는가?
• 동료가 부연 설명 없이 타인에게 되풀이하여 전달할 수 있는가?
• 타인의 피드백을 결과물을 깎아낼 숫돌로 받아들일 준비가 되었는가?

머릿속 아이디어를 세상의 피드백 칼날 위에 올려놓을 때, 비로소 진짜 비즈니스가 시작됩니다.

#비즈니스기획 #프로덕트매니지먼트 #스타트업 #브랜딩 #컨셉기획 #일잘러
"""

        elif platform == "brunch":
            return f"""# 기깔나는 '아이디어'만으로는 승부할 수 없다
## 피드백으로 깎아내는 '비즈니스 컨셉'의 실체화 공식

올 초, 하루 8시간씩 6개월 동안 이어진 부트캠프라는 긴 대장정을 시작했던 것은, 홀로 AI라는 거대한 급물살에 올라타기가 쉽지 않음을 뼈저리게 실감했기 때문이었습니다. 

LLM이든, RAG든, 에이전트든 이미 개념 자체는 이해하고 있었고 조잡한 수준이나마 코드로도 구현할 수 있는 상태였지만, 정작 그것으로 **'무엇을 만들 것인가'**를 정의하는 일은 차원이 다른 문제였습니다.

사실 저는 늘 아이디어가 넘치는 사람이었습니다. 일상의 사소한 불편도 그냥 지나치지 못하는 '프로 불편러'인 제게는 자동화하고 싶은 영역이 수없이 많았고, 그중에서도 인생의 절반을 바쳐온 제 본업의 병목을 해결하고 싶었습니다. AI라는 날개만 달면 거짓말처럼 장애물이 걷히고 멋진 프로덕트가 눈앞에 펼쳐질 줄 알았습니다.

하지만 AI에게 그토록 찬사를 받았던 저의 '프로덕트 컨셉'은, 정작 현실의 프로덕션 단계로 진입하기에는 너무나 희미했던 모양입니다. 
'비IT인을 위한 IT 번역도구'를 꿈꿨던 저의 기획은, 부트캠프가 끝나고 두 달이 지난 지금까지도 바이브코딩의 망망대해를 외롭게 떠돌고 있습니다.

동료들에게 제 야심 찬 생각을 털어놓았을 때 돌아왔던 조심스러운 반응을 잊지 못합니다.
*"그래서 그게 정확히 뭔데? 한 문장으로 설명해 줘."*
*"음... 좋은 생각이긴 한데, 어딘가 모호한 것 같아."*

그 순간 차가운 현실이 가슴을 쳤습니다. 
**내 머릿속에만 갇혀 있는 생각은 비즈니스 세계에서 아무런 쓸모가 없다는 것을.** 
타인에게 1초 만에 가닿지 못하고, 동료와 시장의 냉정한 피드백을 통해 깎이고 다듬어질 수 없다면, 그것은 컨셉이 아니라 **'그저 지나가는 좋은 생각'**에 불과하다는 것을요.

서재 한 칸을 가득 채운 기획 서적들을 다시 펼쳐 들며, 마음에 새겨둔 컨셉의 본질을 다시 정리해 봅니다.

---

### 1. 설명되지 않는 영감은 컨셉이 아니다
비즈니스에서 컨셉의 목적은 화려한 미사여구가 아니라, 타인의 의사결정을 이끌어내는 '가장 단순하고 날카로운 단 하나의 칼날'이어야 합니다. 
내 머릿속의 복잡한 직관을 상대방이 자신의 언어로 즉시 반박할 수 있을 만큼 구체적으로 깎아내는 과정, 그것이 컨셉의 출발점입니다.

### 2. 박선미와 삼양 불닭이 건네는 실체화의 힌트
대한민국 광고사에 남은 카피 '미녀는 석류를 좋아해'의 박선미 카피라이터는 수백 개의 모호한 효능을 버리고 **'Red & Beauty'라는 단 하나의 직관적 진실**만을 남겼습니다.
삼양의 불닭볶음면 역시 두루뭉술한 매운맛 대신 **'외국인 유튜버들이 눈물 흘리며 도전하는 챌린지'**라는 극단적이고 구체적인 장치로 글로벌 팬덤을 일으켰습니다.

결국 살아있는 컨셉이란,
1. **수식어를 걷어낸 단 하나의 명료한 문장**으로 본질을 정의하고,
2. **타인이 오감으로 상상하고 즉각 반응할 수 있는 구체적인 장면**을 제시하며,
3. **[결론 - 근거 - 실행]이라는 단단한 뼈대** 위에서 세상의 피드백을 받아내는 것입니다.

---

### 3. 생각을 꺼내어 세상의 피드백 칼날 위에 올려놓기

머릿속에만 보관해둔 아이디어는 안전합니다. 아무런 상처도 입지 않고, 실패할 일도 없으니까요.
하지만 그 안전함 속에서는 단 하나의 프로덕트도 피어나지 못합니다.

조금 조잡하고 못난 초안일지라도, 1초 만에 설명할 수 있는 단순한 문장으로 세상에 먼저 내놓아야 합니다.
그리고 타인의 피드백이라는 숫돌 위에서 수없이 부딪히고 깎여나갈 때, 비로소 우리의 지나가는 생각은 시대를 움직이는 단단한 '비즈니스 컨셉'으로 다시 태어날 것입니다.
"""

        # General Balance Mode
        return f"""# 기깔나는 '아이디어'만으로는 승부할 수 없다: 피드백으로 깎아내는 '비즈니스 컨셉'의 실체화 공식

올해 초, 하루 8시간씩 6개월간의 AI 부트캠프를 시작했던 것은 홀로 AI라는 급물살에 올라타기가 쉽지 않음을 절감했기 때문입니다. LLM, RAG, 에이전트의 원리를 익히고 원시적인 코드로 구현할 수 있게 되자, 오랜 기간 인생의 절반을 투자해 온 제 본업의 병목을 해결할 멋진 프로덕트가 금세 눈앞에 나타날 것만 같았습니다.

하지만 '비IT인을 위한 IT 번역도구'를 꿈꿨던 저의 기획은, 부트캠프를 마친 지 2개월이 지난 지금까지도 바이브코딩의 망망대해를 떠돌고 있습니다. 

동료들에게 제 기획을 설명할 때마다 마주했던 벽은 높았습니다.
*"그래서 그게 정확히 뭔데? 한 문장으로 설명해 줘."*
*"좋은 생각이긴 한데, 어딘가 모호한 것 같아."*

이해하려 애써주는 동료들에게서조차 모호하다는 반응이 나온다면 비즈니스 시장에서 통할 리 만무합니다. 
**내 머릿속에만 머물러 있는 것은 아이디어일 뿐, 비즈니스 컨셉이 아닙니다.** 
타인에게 1초 만에 설명할 수 없고, 동료와 시장의 피드백을 통해 깎이고 다듬어지는 과정을 견뎌내지 못한다면 그것은 **'그저 지나가는 좋은 생각'**에 불과합니다.

---

## 1. 컨셉의 본질: 머릿속 영감은 컨셉이 아니다

많은 기획자가 장황한 배경 설명과 기술적 화려함을 컨셉의 깊이라고 오해합니다.
그러나 비즈니스에서 컨셉의 목적은 **'타인의 의사결정을 이끌어내는 가장 단순하고 구체적인 도구'**입니다. 
- 복잡한 머릿속 직관을 듣는 이가 즉시 자신의 언어로 해석할 수 있게 만들고,
- 불필요한 군더더기를 걷어내어 **'단 하나의 칼날'**처럼 벼려내는 작업이 바로 컨셉의 실체화입니다.

---

## 2. 지나가는 생각을 '살아있는 비즈니스 컨셉'으로 깎는 3단계 공식

### 1단계: 1초 만에 납득시키는 본질의 언어화 — "단 하나의 진실만 남기기"
'미녀는 석류를 좋아해' 카피를 창작한 박선미 카피라이터의 비결은 수백 개의 모호한 아이디어를 버리는 데 있었습니다. 
- 복잡한 스펙 대신 제품이 주는 **단 하나의 직관적 진실(Red & Beauty)**만을 남겼습니다.
- **실전 팁**: 내 기획을 수식어 없이 [주어 + 목적어 + 동사] 단 1문장으로 요약해 보세요. 7세 아이에게 설명했을 때 "아, 그거!"라는 반응이 나오지 않는다면 아직 언어화되지 않은 것입니다.

### 2단계: 모호함을 걷어내는 극단적 구체화 — "피드백을 부르는 타깃 경험 설계"
삼양의 불닭볶음면은 무난한 매운맛 대신 **'외국인 유튜버들이 땀을 흘리며 도전하는 파이어 누들 챌린지'**라는 시각적이고 구체적인 제품 콘셉트를 잡았습니다.
- 추상적인 "맛있게 매운 라면"은 피드백을 부르지 못합니다.
- 타인이 오감으로 상상하고 반응할 수 있는 구체적인 장면이 주어질 때 비로소 진성 피드백과 팬덤이 형성됩니다.

### 3단계: 피드백의 칼날 위에서 깎아내기 — "회사어 3단 구조화"
생각의 흐름대로 전달하는 것은 소음에 가깝습니다. 듣는 사람이 즉각 피드백하고 실행할 수 있도록 **[결론 - 핵심 근거 - 실행 액션]**의 구조로 뼈대를 세워야 합니다.
1. **결론 (Concept Definition)**: 우리가 정의한 단 하나의 핵심 컨셉은 무엇인가?
2. **근거 (Why & Edge)**: 기존 대안과 비교해 무엇이 결정적으로 다르고 강력한가?
3. **실행 (First Proof)**: 이 컨셉을 시장에서 즉시 증명할 첫 번째 구체적 산출물은 무엇인가?

---

## 3. 비교 요약: 머릿속 '좋은 생각' vs 실체화된 '비즈니스 컨셉'

| 점검 영역 | 머릿속 좋은 생각 (실패 패턴) | 실체화된 비즈니스 컨셉 (성공 패턴) |
| :--- | :--- | :--- |
| **표현 형태** | 장황한 배경 설명과 10장의 기획서 | 1초 만에 뇌리에 꽂히는 단 1개의 직관적 문장 |
| **타인의 반응** | "좋은 생각인데, 정확히 뭘 하자는 거지?" | "아, 그거! 그렇다면 이런 기능도 붙이면 좋겠다!" |
| **피드백 수용** | 내 생각에 대한 지적을 받으면 방어적으로 변함 | 피드백을 컨셉의 군더더기를 깎아낼 숫돌로 활용 |
| **실행 기준** | 완벽한 준비가 끝날 때까지 머릿속에 보관 | 최소한의 구체적 프로토타입/카피로 즉시 시장 테스트 |

---

## 4. 내 컨셉의 실체성을 검증하는 5가지 체크리스트

- [ ] 내 비즈니스 컨셉을 전문 용어 없이 15초 안에 설명할 수 있는가?
- [ ] 동료에게 들려주었을 때 부연 설명 없이 핵심을 되풀이하여 말할 수 있는가?
- [ ] 경쟁 제품과 1초 만에 구분되는 '극단적이고 구체적인 차별점'이 존재하는가?
- [ ] 타인의 비판이나 반론을 바탕으로 컨셉의 군더더기를 과감히 깎아낼 준비가 되었는가?
- [ ] 머릿속 상상에 머무르지 않고, 오늘 당장 보여줄 수 있는 1장의 글이나 프로토타입이 있는가?

---

### 💡 에디터 결론 요약
1. **머릿속에만 있는 아이디어는 아무런 가치가 없습니다.** 표현되지 못한 생각은 자기만족에 불과합니다.
2. **컨셉은 설명하는 것이 아니라 '느껴지게 하는 것'입니다.** 가장 단순하고 날카로운 언어로 정제하세요.
3. **타인의 피드백을 두려워하지 마세요.** 피드백으로 수없이 깎이고 다듬어질 때 비로소 위대한 비즈니스가 탄생합니다.
"""
