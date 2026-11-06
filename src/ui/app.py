"""Streamlit Web Studio (v2.0): 4-Tab Local AI Content Studio.

Tab 1: 작업 모니터 (Job Monitor & Corpus Browser)
Tab 2: 초안 생성 (Draft Generator & Seed Preview)
Tab 3: Seed 이미지 뷰어 & 마크다운 에디터 (Studio View with Lightbox)
Tab 4: 나의 결과물 & 스타일 학습소 (My Corpus & Style Learning)
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path so 'src' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.config import load_config, load_env_file
# Ensure .env is loaded before anything else
load_env_file()
from src.extraction.batch_extractor import BatchMetadataExtractor
from src.extraction.llm_client import LLMClient
from src.ingestion.scanner import IngestionScanner
from src.models import ArticleArchetype, UserStyleProfile
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.synthesis.proofreader import ArticleProofreader
from src.synthesis.style_learner import StyleLearner
from src.synthesis.synthesizer import ArticleSynthesizer

# Page configuration
st.set_page_config(
    page_title="Seed Content Studio",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# App state and initialization
def get_services():
    config = load_config()
    config.ensure_directories()
    init_db(config.paths.db_path)
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)

    # 1. 색인/추출 전용 LLM (기본: 3.5 Flash-Lite, Low Thinking)
    extract_model = os.getenv("EXTRACTION_MODEL", "gemini-3.5-flash-lite")
    extract_effort = os.getenv("EXTRACTION_THINKING_LEVEL", "low")
    extract_llm = LLMClient(model=extract_model)
    extract_llm.set_thinking_level(extract_effort)

    # 2. 초안 기획/합성 전용 LLM (기본: 3.8 Flash, Medium Thinking)
    synth_model = os.getenv("SYNTHESIS_MODEL", "gemini-3.8-flash")
    synth_effort = os.getenv("SYNTHESIS_THINKING_LEVEL", "medium")
    synth_llm = LLMClient(model=synth_model)
    synth_llm.set_thinking_level(synth_effort)

    # 3. 검토/퇴고 전용 LLM (기본: 3.8 Pro, High Thinking)
    proof_model = os.getenv("PROOFREADING_MODEL", "gemini-3.8-pro")
    proof_effort = os.getenv("PROOFREADING_THINKING_LEVEL", "high")
    proof_llm = LLMClient(model=proof_model)
    proof_llm.set_thinking_level(proof_effort)

    retriever = SeedRetriever(config=config, repo=repo)
    synthesizer = ArticleSynthesizer(config=config, repo=repo, llm_client=synth_llm)
    style_learner = StyleLearner(config=config, repo=repo, llm_client=synth_llm)
    scanner = IngestionScanner(config=config, repo=repo)
    extractor = BatchMetadataExtractor(config=config, repo=repo, llm_client=extract_llm)
    proofreader = ArticleProofreader(config=config, llm_client=proof_llm)
    return config, repo, extract_llm, synth_llm, proof_llm, retriever, synthesizer, style_learner, scanner, extractor, proofreader

config, repo, extract_llm, synth_llm, proof_llm, retriever, synthesizer, style_learner, scanner, extractor, proofreader = get_services()


def resolve_asset_path(raw_path: str) -> Optional[Path]:
    """Resolve asset relative path to absolute filesystem path."""
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_absolute() and p.exists():
        return p
    candidate = config.paths.assets_dir / raw_path
    if candidate.exists():
        return candidate
    candidate = Path("data/processed/assets") / raw_path
    if candidate.exists():
        return candidate
    if p.exists():
        return p
    return None


@st.dialog("🖼️ 시각 자료 원본 상세 (Lightbox)", width="large")
def show_lightbox_dialog(img_path: str, asset_id: str, doc_id: str, page_no: int, caption: str, doc_title: str):
    """Lightbox modal dialog for full-size visual asset preview."""
    st.image(img_path, caption=caption or f"[{asset_id}] (p.{page_no})", use_container_width=True)
    st.markdown(f"**출처 문서**: Seed #{doc_id} (`{doc_title}`) | **페이지**: p.{page_no} | **식별자**: `{asset_id}`")
    if caption:
        st.info(f"**원문 캡션**: {caption}")
    st.markdown("**본문 삽입용 마크다운 코드 (복사하여 에디터에 삽입)**:")
    callout = f"> 🖼️ **[시각 자료 제안 | Seed #{doc_id} - {asset_id}]**: {caption or doc_title}"
    st.code(callout, language="markdown")


# Session State defaults
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

studio_password = os.getenv("STUDIO_PASSWORD", "").strip()

# P0-1: Authentication Gate (Public IP Access Protection)
if studio_password and not st.session_state["authenticated"]:
    st.markdown(
        """
        <style>
        .auth-card {
            max-width: 440px;
            margin: 60px auto;
            padding: 30px;
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.title("🔒 Seed Content Studio")
        st.markdown("**비공개 작업 스튜디오**입니다. 접근 비밀번호를 입력해주세요.")
        with st.form("auth_form", clear_on_submit=False):
            pwd_input = st.text_input("스튜디오 비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submit_btn = st.form_submit_button("스튜디오 입장", use_container_width=True, type="primary")
            if submit_btn:
                if pwd_input == studio_password:
                    st.session_state["authenticated"] = True
                    st.success("인증 완료. 스튜디오에 입장합니다...")
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

if "active_creation_id" not in st.session_state:
    st.session_state["active_creation_id"] = None
if "editor_text" not in st.session_state:
    st.session_state["editor_text"] = ""
if "notes_text" not in st.session_state:
    st.session_state["notes_text"] = ""
if "t2_step" not in st.session_state:
    st.session_state["t2_step"] = 1
if "t2_topic" not in st.session_state:
    st.session_state["t2_topic"] = ""
if "t2_direction" not in st.session_state:
    st.session_state["t2_direction"] = ""
if "t2_seeds" not in st.session_state or st.session_state["t2_seeds"] is None:
    st.session_state["t2_seeds"] = []
if "t2_blueprint" not in st.session_state:
    st.session_state["t2_blueprint"] = None

# Sidebar: Environment & Studio Status
with st.sidebar:
    st.header("⚙️ 스튜디오 환경 & 제어")

    has_gemini = bool(os.getenv("GEMINI_API_KEY") or (getattr(extract_llm, "provider", "") == "gemini" and getattr(extract_llm, "api_key", None)))
    has_openai = bool(os.getenv("OPENAI_API_KEY") or (getattr(extract_llm, "provider", "") == "openai" and getattr(extract_llm, "api_key", None)))

    if has_gemini:
        st.success("🟢 Gemini 실시간 AI 엔진 활성")
    elif has_openai:
        st.success("🟢 OpenAI 실시간 AI 엔진 활성")
    else:
        st.warning("⚠️ API 키 미설정\n(.env 파일에 GEMINI_API_KEY를 설정해 주세요.)")

    # Current Per-Task Model Status
    st.markdown("#### 🧠 작업별 AI 모델 현황")
    st.markdown(
        f"""
- 📑 **색인/추출**: `{extract_llm.model}` (`{extract_llm.thinking_level.upper()}`)
- ✍️ **초안 생성**: `{synth_llm.model}` (`{synth_llm.thinking_level.upper()}`)
- 🔍 **검토/퇴고**: `{proof_llm.model}` (`{proof_llm.thinking_level.upper()}`)
"""
    )

    model_options = [
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.8-pro",
        "gemini-2.0-flash",
        "gpt-4o-mini",
        "gpt-4o",
    ]
    effort_options = ["low", "medium", "high"]
    effort_labels = {
        "low": "⚡ Low (빠른 속도 & 대량 처리)",
        "medium": "⚖️ Medium (균형 - 일상 초안)",
        "high": "🧠 High (심층 사유 & 정밀도)",
    }

    # Helper function to save per-task models to .env
    def _save_task_models(e_m, e_l, s_m, s_l, p_m, p_l):
        extract_llm.model = e_m
        extract_llm.set_thinking_level(e_l)
        extractor.llm_client.model = e_m
        extractor.llm_client.set_thinking_level(e_l)

        synth_llm.model = s_m
        synth_llm.set_thinking_level(s_l)
        synthesizer.llm_client.model = s_m
        synthesizer.llm_client.set_thinking_level(s_l)
        style_learner.llm_client.model = s_m
        style_learner.llm_client.set_thinking_level(s_l)

        proof_llm.model = p_m
        proof_llm.set_thinking_level(p_l)
        proofreader.llm_client.model = p_m
        proofreader.llm_client.set_thinking_level(p_l)

        env_path = Path(".env")
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
            skip_prefixes = [
                "EXTRACTION_MODEL=", "EXTRACTION_THINKING_LEVEL=",
                "SYNTHESIS_MODEL=", "SYNTHESIS_THINKING_LEVEL=",
                "PROOFREADING_MODEL=", "PROOFREADING_THINKING_LEVEL="
            ]
            new_lines = [l for l in lines if not any(l.startswith(p) for p in skip_prefixes)]
            new_lines.extend([
                f"EXTRACTION_MODEL={e_m}",
                f"EXTRACTION_THINKING_LEVEL={e_l}",
                f"SYNTHESIS_MODEL={s_m}",
                f"SYNTHESIS_THINKING_LEVEL={s_l}",
                f"PROOFREADING_MODEL={p_m}",
                f"PROOFREADING_THINKING_LEVEL={p_l}",
            ])
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Granular Per-Task Model Configuration
    with st.expander("🎛️ 작업별 AI 모델 상세 설정", expanded=False):
        st.caption("색인, 초안 생성, 퇴고 단계에 각기 다른 최적 모델을 독립적으로 지정할 수 있습니다.")

        st.markdown("**📑 1. 색인 & 메타데이터 추출 (Tab 1)**")
        cur_e_idx = model_options.index(extract_llm.model) if extract_llm.model in model_options else 0
        cfg_ext_m = st.selectbox("색인 모델", options=model_options, index=cur_e_idx, key="cfg_ext_m", help="대량 파일 인제스천에 최적화된 경량 모델 추천")
        cfg_ext_e = st.select_slider("색인 추론 강도", options=effort_options, value=extract_llm.thinking_level, format_func=lambda x: effort_labels.get(x, x), key="cfg_ext_e")

        st.markdown("---")
        st.markdown("**✍️ 2. 초안 기획 & 본문 합성 (Tab 2)**")
        cur_s_idx = model_options.index(synth_llm.model) if synth_llm.model in model_options else 1
        cfg_syn_m = st.selectbox("초안 모델", options=model_options, index=cur_s_idx, key="cfg_syn_m", help="논리 전개 및 문맥 합성력이 뛰어난 Flash/Pro 모델 추천")
        cfg_syn_e = st.select_slider("초안 추론 강도", options=effort_options, value=synth_llm.thinking_level, format_func=lambda x: effort_labels.get(x, x), key="cfg_syn_e")

        st.markdown("---")
        st.markdown("**🔍 3. 검토 & 에디토리얼 퇴고 (Tab 3)**")
        cur_p_idx = model_options.index(proof_llm.model) if proof_llm.model in model_options else 2
        cfg_prf_m = st.selectbox("퇴고 모델", options=model_options, index=cur_p_idx, key="cfg_prf_m", help="출판급 문체 다듬기와 정밀 진단이 가능한 Pro/High 모델 추천")
        cfg_prf_e = st.select_slider("퇴고 추론 강도", options=effort_options, value=proof_llm.thinking_level, format_func=lambda x: effort_labels.get(x, x), key="cfg_prf_e")

        if st.button("💾 작업별 모델 설정 저장 & 적용", use_container_width=True, type="primary"):
            _save_task_models(cfg_ext_m, cfg_ext_e, cfg_syn_m, cfg_syn_e, cfg_prf_m, cfg_prf_e)
            st.success("🎉 작업별 맞춤 모델 설정이 저장 및 적용되었습니다!")
            st.rerun()

    # Recommended 1-Click Preset Pairs
    with st.expander("🎯 추천 프리셋 페어 (1-Click)", expanded=False):
        if st.button("🚀 [추천 황금 조합]\n색인: Lite / 초안: Flash / 검토: Pro", use_container_width=True):
            _save_task_models("gemini-3.5-flash-lite", "low", "gemini-3.8-flash", "medium", "gemini-3.8-pro", "high")
            st.success("황금 조합 적용 완료!")
            st.rerun()
        if st.button("⚡ [초고속 절약 페어]\n전 작업 3.5 Flash-Lite 통일", use_container_width=True):
            _save_task_models("gemini-3.5-flash-lite", "low", "gemini-3.5-flash-lite", "low", "gemini-3.5-flash-lite", "low")
            st.success("초고속 절약 페어 적용 완료!")
            st.rerun()
        if st.button("💎 [최고급 출판 페어]\n전 작업 3.8 Pro 통일", use_container_width=True):
            _save_task_models("gemini-3.8-pro", "high", "gemini-3.8-pro", "high", "gemini-3.8-pro", "high")
            st.success("최고급 출판 페어 적용 완료!")
            st.rerun()

    with st.expander("🔑 Gemini / OpenAI API 키 설정", expanded=not (has_gemini or has_openai)):
        st.caption("Google AI Studio (aistudio.google.com)에서 발급받은 무료 Gemini API Key를 입력하시면 즉시 실시간 Gemini 3.8 / 3.x 모델로 연결됩니다.")
        api_input = st.text_input(
            "Gemini API Key (또는 OpenAI)",
            type="password",
            value=os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
            placeholder="AIzaSy... 또는 sk-...",
        )
        if st.button("💾 API 키 저장 & 적용", use_container_width=True):
            if api_input:
                provider = "openai" if api_input.startswith("sk-") else "gemini"
                if provider == "gemini":
                    os.environ["GEMINI_API_KEY"] = api_input
                else:
                    os.environ["OPENAI_API_KEY"] = api_input

                # Persist to .env
                env_path = Path(".env")
                env_lines = []
                if env_path.exists():
                    env_lines = env_path.read_text(encoding="utf-8").splitlines()

                key_var = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
                new_lines = [l for l in env_lines if not l.startswith(f"{key_var}=") and not l.startswith("DEFAULT_LLM_PROVIDER=")]
                new_lines.append(f"{key_var}={api_input}")
                new_lines.append(f"DEFAULT_LLM_PROVIDER={provider}")
                env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

                extract_llm.set_api_key(api_input, provider=provider)
                synth_llm.set_api_key(api_input, provider=provider)
                proof_llm.set_api_key(api_input, provider=provider)
                extractor.llm_client.set_api_key(api_input, provider=provider)
                synthesizer.llm_client.set_api_key(api_input, provider=provider)
                style_learner.llm_client.set_api_key(api_input, provider=provider)
                proofreader.llm_client.set_api_key(api_input, provider=provider)
                st.success(f"🎉 {provider.upper()} API 키가 저장 및 활성화되었습니다!")
                st.rerun()

    st.divider()
    st.subheader("📊 스튜디오 현황")
    st.metric("색인된 Seed 아티클", f"{len(repo.list_articles())}편")
    fin_list = repo.list_creations(status="FINALIZED")
    st.metric("확정된 나만의 아티클", f"{len(fin_list)} / 5편")
    if len(fin_list) >= 5:
        st.success("🎉 스타일 프로필 활성화 완료!")
    else:
        st.caption(f"💡 앞으로 {5 - len(fin_list)}편 더 확정 시 나만의 문체 스타일이 AI에 완전 동기화됩니다.")

    # Fallback alerts per service
    for stage_lbl, cl in [("색인", extract_llm), ("초안", synth_llm), ("퇴고", proof_llm)]:
        if getattr(cl, "last_fallback_info", None):
            st.info(f"⚡ [{stage_lbl}] {cl.last_fallback_info}")

    if studio_password:
        st.divider()
        if st.button("🔒 스튜디오 잠금 (로그아웃)", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

st.title("🌱 Seed Synthesis Content Studio")
st.caption("초안 복제를 방지하는 탈색(Distillation) 기반 상호보완 아티클 스튜디오 & 나만의 스타일 학습 루프")

tabs = st.tabs([
    "📊 작업 모니터",
    "✍️ 초안 생성",
    "🎨 Seed 뷰어 & 에디터",
    "📚 나의 결과물 & 스타일 학습소",
])

# -------------------------------------------------------------
# TAB 1: 작업 모니터 (Job Monitor & Corpus Browser)
# -------------------------------------------------------------
with tabs[0]:
    t1_c1, t1_c2 = st.columns([3, 1])
    with t1_c1:
        st.header("1. 파이프라인 실시간 모니터링 & Seed 코퍼스")
    with t1_c2:
        st.info(f"📑 색인 AI: `{extract_llm.model}` ({extract_llm.thinking_level.upper()})")

    # Inbound Direct Uploader (P0-2)
    with st.expander("📥 신규 문서 브라우저 직접 업로드 (Web Drag & Drop Ingestion)", expanded=True):
        st.caption("PDF, DOCX, TXT, 마크다운(MD) 문서를 여기에 끌어다 놓으면 서버 `data/inbox/`로 즉시 저장되고 색인 파이프라인을 실행할 수 있습니다.")
        uploaded_files = st.file_uploader(
            "문서 파일 선택 또는 드래그앤드롭",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key="inbox_direct_uploader",
            help="여러 파일을 동시에 선택하거나 탐색기에서 드래그하여 업로드할 수 있습니다.",
        )
        if uploaded_files:
            up_col1, up_col2 = st.columns([3, 1])
            with up_col1:
                st.info(f"선택된 파일: **{len(uploaded_files)}개** ({', '.join(f.name for f in uploaded_files)})")
            with up_col2:
                if st.button("⚡ 서버 저장 & 즉시 색인", type="primary", use_container_width=True):
                    inbox_dir = config.paths.inbox_dir
                    inbox_dir.mkdir(parents=True, exist_ok=True)
                    saved_count = 0
                    for uf in uploaded_files:
                        dest_path = inbox_dir / uf.name
                        dest_path.write_bytes(uf.getbuffer())
                        saved_count += 1

                    with st.status(f"{saved_count}개 문서 업로드 완료. 중복 검사 및 파이프라인 처리 중...", expanded=True) as status_box:
                        st.write("1단계: Inbox 스캔 및 중복 문서 검증 중...")
                        scanner.scan_inbox(move_archive=True)
                        new_records = scanner.last_newly_processed
                        skipped_dups = scanner.last_skipped_duplicates

                        if skipped_dups:
                            for s in skipped_dups:
                                st.warning(f"⏩ **[중복 건너뜀]** `{s['file']}` → 기존 Seed #{s['doc_id']} ('{s['title']}')와 {s['reason']}")

                        st.write(f"  └ 신규 수집: **{len(new_records)}건**, 중복 제외: **{len(skipped_dups)}건**")

                        if len(new_records) > 0:
                            st.write(f"2단계: 신규 문서 메타데이터 추출 및 FTS5 색인 중... (AI 모델: {extract_llm.model})")
                            new_doc_ids = [r.doc_id for r in new_records]
                            indexed_records = extractor.run_sync(doc_ids=new_doc_ids)
                            st.write(f"  └ {len(indexed_records)}건 신규 색인 완료")
                            status_box.update(label="🎉 신규 문서 색인 완료!", state="complete", expanded=False)
                            st.success(f"신규 {len(indexed_records)}건의 문서가 정상적으로 색인되었습니다.")
                        else:
                            st.write("2단계: 신규 문서가 없으므로 AI 호출(토큰 소진)을 자동으로 건너뛰었습니다.")
                            status_box.update(label="ℹ️ 모든 문서가 중복으로 확인되어 색인이 건너뛰어졌습니다.", state="complete", expanded=False)
                            st.info("💡 업로드된 파일이 이미 데이터베이스에 존재하여 불필요한 AI 호출 없이 건너뛰었습니다.")
                    st.rerun()

    st.markdown("---")
    col_act1, col_act2, col_act3 = st.columns([2, 2, 4])
    with col_act1:
        if st.button("📥 Inbox 신규 파일 수집 (Ingest)", use_container_width=True):
            with st.spinner("Inbox 스캔 및 텍스트/이미지 추출 중..."):
                scanner.scan_inbox(move_archive=True)
                new_cnt = len(scanner.last_newly_processed)
                dup_cnt = len(scanner.last_skipped_duplicates)
                st.success(f"수집 완료: 신규 {new_cnt}건 처리됨 (중복 {dup_cnt}건 제외)")
                st.rerun()
    with col_act2:
        if st.button("🧠 미색인 문서 메타데이터 추출 (Extract)", use_container_width=True):
            with st.spinner("비동기 메타데이터 추출 및 FTS5 색인 중..."):
                indexed = extractor.run_sync()
                st.success(f"색인 완료: {len(indexed)}건 새로 등록됨")
                st.rerun()

    st.subheader("최근 파이프라인 작업 로그 (`pipeline_jobs`)")
    jobs = repo.list_jobs(limit=15)
    if jobs:
        st.dataframe(
            [
                {
                    "작업 ID": j["job_id"],
                    "종류": j["job_type"],
                    "상태": j["status"],
                    "진행도": f"{j['processed_items']}/{j['total_items']}",
                    "실패": j["failed_items"],
                    "최근 문서": j["current_doc_id"],
                    "로그 요약": j["log_summary"],
                    "시작 시간": j["started_at"],
                }
                for j in jobs
            ],
            use_container_width=True,
        )
        with st.expander("🗑️ 파이프라인 작업 로그 삭제 관리", expanded=False):
            j_col1, j_col2 = st.columns([3, 1])
            with j_col1:
                selected_job_to_del = st.selectbox(
                    "삭제할 작업 로그 선택",
                    options=[j["job_id"] for j in jobs],
                    format_func=lambda jid: f"[{jid}] {next((j['job_type'] + ' (' + j['status'] + ')' for j in jobs if j['job_id'] == jid), '')}",
                )
            with j_col2:
                if st.button("🗑️ 선택 로그 삭제", use_container_width=True):
                    if repo.delete_job(selected_job_to_del):
                        st.success(f"작업 로그 `{selected_job_to_del}`가 삭제되었습니다.")
                        st.rerun()
            if st.button("🧹 전체 작업 로그 비우기", use_container_width=True):
                cnt = repo.delete_all_jobs()
                st.success(f"총 {cnt}건의 작업 로그를 모두 비웠습니다.")
                st.rerun()
    else:
        st.info("실행 대기 중인 파이프라인 작업이 없습니다.")

    st.divider()
    st.subheader("색인 완료된 Seed 아티클 목록")
    articles = repo.list_articles()
    if articles:
        st.caption(f"등록된 Seed 아티클: {len(articles)}편")
        col_list = []
        for art in articles:
            meta = repo.get_article_metadata(art.doc_id)
            col_list.append({
                "Doc ID": art.doc_id,
                "제목": art.title,
                "카테고리": meta.primary_category if meta else "-",
                "아키타입": meta.article_archetype.value if meta else "-",
                "이미지 수": art.image_count,
                "상태": art.status.value,
                "핵심 테제": meta.core_thesis if meta else "-",
            })
        st.dataframe(col_list, use_container_width=True)

        with st.expander("🗑️ Seed 아티클 영구 삭제 관리", expanded=False):
            st.warning("⚠️ Seed 문서를 삭제하면 FTS5 전문 검색 색인, 추출된 이미지 에셋 메타데이터, 전처리 텍스트 파일이 함께 제거됩니다.")
            del_col1, del_col2 = st.columns([3, 1])
            with del_col1:
                selected_doc_to_del = st.selectbox(
                    "삭제할 Seed 문서 선택",
                    options=[a.doc_id for a in articles],
                    format_func=lambda did: f"Seed #{did}: {next((a.title for a in articles if a.doc_id == did), '')}",
                )
                del_files_check = st.checkbox("전처리 마크다운 및 추출 에셋 파일도 함께 삭제", value=True)
            with del_col2:
                if st.button("🗑️ 선택 Seed 삭제", type="secondary", use_container_width=True):
                    if repo.delete_article(selected_doc_to_del, delete_files=del_files_check):
                        st.success(f"Seed #{selected_doc_to_del} 문서와 관련 데이터가 성공적으로 삭제되었습니다.")
                        st.rerun()
    else:
        st.warning("등록된 아티클이 없습니다. run.py ingest를 먼저 실행하세요.")

# -------------------------------------------------------------
# TAB 2: 초안 생성 (Draft Generator)
# -------------------------------------------------------------
with tabs[1]:
    t2_c1, t2_c2 = st.columns([3, 1])
    with t2_c1:
        st.header("2. 상호보완 Seed 선별 및 중립 초안 생성")
    with t2_c2:
        st.info(f"✍️ 초안 AI: `{synth_llm.model}` ({synth_llm.thinking_level.upper()})")

    # Step indicators
    current_step = st.session_state.get("t2_step", 1)
    st.caption("3단계 위저드 방식으로 주제 입력 ➔ Seed/설계도 검토 ➔ 실시간 LLM 초안 집필을 단계별로 진행합니다.")

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.info("💡 **1단계: 주제 & 방향성 입력**" if current_step == 1 else "1단계: 주제 & 방향성")
    with s_col2:
        st.info("📐 **2단계: Seed & 설계도 검토**" if current_step == 2 else "2단계: Seed & 설계도")
    with s_col3:
        st.info("✍️ **3단계: 실시간 초안 집필**" if current_step == 3 else "3단계: 초안 집필")

    st.divider()

    # Step 1: Input Topic & Direction
    if current_step == 1:
        step1_h_col1, step1_h_col2 = st.columns([3, 1])
        with step1_h_col1:
            st.subheader("💡 1단계. 타깃 주제와 나만의 관점/경험담 입력")
        with step1_h_col2:
            if st.button("🧹 새 글 쓰기 (입력 초기화)", help="이전에 입력된 주제와 방향성 메모를 모두 비우고 깨끗한 백지 상태로 시작합니다.", use_container_width=True):
                st.session_state["t2_step"] = 1
                st.session_state["t2_topic"] = ""
                st.session_state["t2_direction"] = ""
                st.session_state["t2_seeds"] = []
                st.session_state["t2_blueprint"] = None
                st.session_state["t2_synthesis_done"] = False
                st.session_state["active_creation_id"] = None
                st.session_state["t2_input_topic"] = ""
                st.session_state["t2_input_direction"] = ""
                st.rerun()

        t_val = st.text_input(
            "새로 작성할 타깃 주제 (Topic)",
            value=st.session_state.get("t2_topic", ""),
            placeholder="예: 생성형 AI 시대, 비즈니스 기획자가 갖춰야 할 진짜 경쟁력",
            key="t2_input_topic",
        )
        d_val = st.text_area(
            "집필 방향 및 나만의 고유한 관점/경험담 (Direction)",
            value=st.session_state.get("t2_direction", ""),
            placeholder="자신만의 주장, 현장 경험, 차별화된 문제의식 등을 자유롭게 서술하세요.",
            height=200,
            key="t2_input_direction",
        )
        st.caption(f"📝 입력 상태: 타깃 주제 **{len(t_val):,}자** | 집필 방향/관점 **{len(d_val):,}자**")

        # Real-time state synchronization: Keep t2_topic and t2_direction up to date
        if t_val != st.session_state.get("t2_topic"):
            st.session_state["t2_topic"] = t_val
        if d_val != st.session_state.get("t2_direction"):
            st.session_state["t2_direction"] = d_val

        col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 1, 1])
        with col_cfg1:
            archetypes = [a.value for a in ArticleArchetype]
            selected_archetype = st.selectbox("목표 아티클 아키타입", ["(자동 추천)"] + archetypes, index=0)
            arch_enum = ArticleArchetype(selected_archetype) if selected_archetype != "(자동 추천)" else None
        with col_cfg2:
            seed_count = st.slider("결합할 Seed 문서 수", min_value=2, max_value=3, value=3)
        with col_cfg3:
            active_profile = style_learner.get_active_profile()
            has_profile = active_profile is not None
            use_style = st.checkbox(
                f"내 스타일 반영 ({f'v{active_profile.profile_version}' if has_profile else '미생성'})",
                value=has_profile,
                disabled=not has_profile,
            )

        if st.button("다음 2단계: 상호보완 Seed 탐색 ➡️", type="primary", use_container_width=True):
            if not t_val.strip():
                st.warning("타깃 주제를 입력해 주세요.")
            else:
                st.session_state["t2_topic"] = t_val
                st.session_state["t2_direction"] = d_val
                st.session_state["t2_arch_enum"] = arch_enum
                st.session_state["t2_use_style"] = use_style

                with st.spinner("🔍 로컬 카탈로그 DB에서 상호보완 Seed 문서를 선별 중입니다..."):
                    candidate_seeds = retriever.select_complementary_seeds(
                        topic=t_val,
                        direction=d_val,
                        target_archetype=arch_enum,
                        count=seed_count,
                    )
                st.session_state["t2_seeds"] = candidate_seeds
                # Reset previous blueprint so stale data is not displayed
                st.session_state["t2_blueprint"] = None
                st.session_state["t2_synthesis_done"] = False
                st.session_state["t2_step"] = 2
                st.rerun()

    # Step 2: Review Seeds & Blueprint
    elif current_step == 2:
        st.subheader("📐 2단계. 선별된 상호보완 Seed 문서 & AI 설계도(Blueprint) 검토")

        cur_t = st.session_state.get("t2_topic", "")
        cur_d = st.session_state.get("t2_direction", "")

        # Target Topic & Context Confirmation Banner (2 distinct cards for clarity)
        col_banner1, col_banner2 = st.columns([1, 1])
        with col_banner1:
            st.markdown(
                f"""
                <div style="background-color: rgba(30, 136, 229, 0.08); border-left: 4px solid #1E88E5; padding: 12px 16px; border-radius: 6px; height: 100%;">
                    <div style="font-size: 12px; font-weight: 700; color: #1565C0; margin-bottom: 4px;">🎯 1단계 타깃 주제 (Topic) <span style="font-size: 11px; font-weight: 400; color: #666;">({len(cur_t):,}자)</span></div>
                    <div style="font-size: 15px; font-weight: 700; color: #111; line-height: 1.4;">{cur_t or '(주제 미지정)'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_banner2:
            st.markdown(
                f"""
                <div style="background-color: rgba(67, 160, 71, 0.08); border-left: 4px solid #43A047; padding: 12px 16px; border-radius: 6px; height: 100%;">
                    <div style="font-size: 12px; font-weight: 700; color: #2E7D32; margin-bottom: 4px;">🧭 나만의 집필 방향 및 고유 관점 (Context) <span style="font-size: 11px; font-weight: 400; color: #666;">({len(cur_d):,}자)</span></div>
                    <div style="font-size: 13px; color: #222; line-height: 1.5; max-height: 120px; overflow-y: auto; white-space: pre-wrap;">{cur_d or '(관점 미지정 - 기본 아키타입 적용)'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.write("")

        c_seeds = st.session_state.get("t2_seeds") or []
        bp = st.session_state.get("t2_blueprint")

        col_s_left, col_s_right = st.columns([1, 1])
        with col_s_left:
            st.markdown("#### 📚 선별된 상호보완 Seed 문서")
            if c_seeds:
                for s in c_seeds:
                    with st.expander(f"[{s.seed_type}] Seed #{s.doc_id}: {s.title}", expanded=True):
                        st.markdown(f"**역할 및 선정 사유:** {s.reason}")
                        if s.metadata:
                            st.markdown(f"**핵심 관점 전환:** {s.metadata.reframing_logic}")
                            st.markdown(f"**핵심 테제:** {s.metadata.core_thesis}")
                            st.caption(f"태그: {', '.join(s.metadata.topic_tags)}")
            else:
                st.info("선별된 Seed 문서가 없습니다.")

        with col_s_right:
            st.markdown("#### 🗺️ AI 합성 설계도 (Synthesis Blueprint)")
            curr_m = getattr(synth_llm, "model", "Gemini")
            if bp:
                st.success(f"**제안 제목:** {bp.proposed_title}")
                st.markdown(f"**타깃 독자:** {bp.target_reader_definition}")
                st.markdown(f"**융합 관점 전환:** {bp.synthesized_reframing}")
                st.markdown("**목차 및 섹션 아웃라인:**")
                for sec in bp.section_outline:
                    st.write(f"- {sec}")
            else:
                st.info(
                    f"💡 좌측의 상호보완 Seed 문서 {len(c_seeds)}건이 준비되었습니다.\n\n"
                    f"아래 버튼을 누르면 AI 모델(`{curr_m}`)이 고유 관점과 Seed를 융합하여 맞춤형 설계도를 기획합니다."
                )
                if st.button("🤖 AI 합성 설계도 기획 시작 (약 5~10초 소요)", type="primary", use_container_width=True):
                    with st.spinner(f"🤖 {curr_m} 모델이 상호보완 Seed를 융합하여 맞춤형 설계도를 기획 중입니다... (최대 30초 대기)"):
                        try:
                            bp = synthesizer.planner.plan_blueprint_sync(
                                topic=cur_t,
                                direction=cur_d,
                                seeds=c_seeds,
                                archetype=st.session_state.get("t2_arch_enum"),
                            )
                            st.session_state["t2_blueprint"] = bp
                            st.success("✅ AI 합성 설계도 기획 완료!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ AI 설계도 기획 중 오류가 발생했습니다: {e}")
                            st.warning("Google Gemini API 통신 지연 또는 일시 혼잡일 수 있습니다. 사이드바에서 다른 모델(예: gemini-3.5-flash-lite)을 선택하거나 잠시 후 다시 시도해 주세요.")

        st.divider()
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 2])
        with col_nav1:
            if st.button("⬅️ 1단계로 돌아가서 수정", use_container_width=True):
                st.session_state["t2_step"] = 1
                st.rerun()
        with col_nav2:
            if st.button("🔄 AI 설계도 다시 기획", disabled=(bp is None), use_container_width=True):
                with st.spinner(f"AI({curr_m})가 새로운 관점의 설계도를 다시 기획 중입니다..."):
                    try:
                        new_bp = synthesizer.planner.plan_blueprint_sync(
                            topic=cur_t,
                            direction=cur_d,
                            seeds=c_seeds,
                            archetype=st.session_state.get("t2_arch_enum"),
                        )
                        st.session_state["t2_blueprint"] = new_bp
                        st.success("새로운 설계도가 생성되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ 다시 기획 중 오류 발생: {e}")
        with col_nav3:
            if st.button("🧹 처음부터 새로 작성", use_container_width=True):
                st.session_state["t2_step"] = 1
                st.session_state["t2_topic"] = ""
                st.session_state["t2_direction"] = ""
                st.session_state["t2_seeds"] = []
                st.session_state["t2_blueprint"] = None
                st.session_state["t2_synthesis_done"] = False
                st.session_state["active_creation_id"] = None
                st.session_state["t2_input_topic"] = ""
                st.session_state["t2_input_direction"] = ""
                st.rerun()
        with col_nav4:
            if st.button(
                "다음 3단계: AI 중립 초안 집필 시작 🚀",
                type="primary",
                disabled=(bp is None),
                use_container_width=True,
                help="설계도를 먼저 생성해야 3단계로 진행할 수 있습니다." if bp is None else None,
            ):
                st.session_state["t2_step"] = 3
                st.session_state["t2_synthesis_done"] = False
                st.rerun()

    # Step 3: Synthesis & Real-time Progress
    elif current_step == 3:
        st.subheader("✍️ 3단계. 실시간 LLM 초안 집필 및 스튜디오 등록")

        t_topic = st.session_state.get("t2_topic", "")
        t_dir = st.session_state.get("t2_direction", "")
        c_seeds = st.session_state.get("t2_seeds") or []
        bp = st.session_state.get("t2_blueprint")
        arch_enum = st.session_state.get("t2_arch_enum")
        use_style = st.session_state.get("t2_use_style", False)
        active_prof = style_learner.get_active_profile() if use_style else None
        curr_m = getattr(synth_llm, "model", "Gemini")

        if not st.session_state.get("t2_synthesis_done", False):
            prog_bar = st.progress(0.15, text="⏳ [1/3] 상호보완 Seed 원문 재료 탈색(Distillation) 진행 중...")
            try:
                # 1. Distillation
                distilled_sheets = synthesizer.distiller.distill_all_sync(c_seeds)
                prog_bar.progress(0.45, text=f"🤖 [2/3] {curr_m} 모델에 설계도와 재료를 전송하여 초안 본문 집필 중... (최대 30초 소요)")

                # 2. Synthesis Call (pass approved blueprint & distilled_sheets directly)
                out_file, content, blueprint, distilled = synthesizer.synthesize_sync(
                    topic=t_topic,
                    direction=t_dir,
                    seeds=c_seeds,
                    archetype=arch_enum,
                    style_profile=active_prof,
                    blueprint=bp,
                    distilled_sheets=distilled_sheets,
                )
                prog_bar.progress(0.9, text="💾 [3/3] 초안 산출물 저장 및 스튜디오 카탈로그 등록 중...")

                # Find the new creation_id
                creations = repo.list_creations(limit=1)
                new_id = creations[0]["creation_id"] if creations else None
                st.session_state["active_creation_id"] = new_id
                st.session_state["_loaded_cid"] = new_id

                # Split frontmatter immediately upon generation
                fm, clean_body = ArticleProofreader.split_frontmatter(content)
                st.session_state["editor_frontmatter"] = fm
                st.session_state["editor_text"] = clean_body
                if new_id:
                    st.session_state[f"editor_area_{new_id}"] = clean_body
                    st.session_state[f"editor_area_side_{new_id}"] = clean_body

                st.session_state["t2_synthesis_done"] = True
                st.session_state["t2_new_id"] = new_id
                st.session_state["t2_out_file_name"] = out_file.name
                st.session_state["t2_content_len"] = len(content)

                prog_bar.progress(1.0, text="🎉 초안 생성이 성공적으로 완료되었습니다!")
                import time
                time.sleep(0.5)
                st.rerun()

            except Exception as e:
                prog_bar.empty()
                st.error(f"⚠️ 초안 집필 중 오류가 발생했습니다: {e}")
                st.warning("Google Gemini API 통신 지연 또는 일시 혼잡일 수 있습니다. 사이드바에서 모델 설정을 점검하거나 다시 시도해 주세요.")
                c_err1, c_err2 = st.columns([1, 1])
                with c_err1:
                    if st.button("🔄 초안 집필 다시 시도", type="primary", use_container_width=True):
                        st.rerun()
                with c_err2:
                    if st.button("⬅️ 2단계 설계도 검토로 돌아가기", use_container_width=True):
                        st.session_state["t2_step"] = 2
                        st.rerun()

        else:
            out_name = st.session_state.get("t2_out_file_name", "draft.md")
            new_id = st.session_state.get("t2_new_id", "cr_unknown")
            c_len = st.session_state.get("t2_content_len", 0)

            st.success(f"🎉 **초안 생성 완료!** 파일: `{out_name}` (식별 ID: `{new_id}` / 본문 {c_len:,}자)")

            c_go1, c_go2, c_go3 = st.columns([2, 1, 1])
            with c_go1:
                st.info("👉 상단 탭에서 **'🎨 3. Seed 뷰어 & 에디터'**를 클릭하면 생성된 초안이 즉시 로드되어 있으며, AI 수석 편집장의 첨삭과 라이트박스 이미지를 함께 보며 퇴고를 진행하실 수 있습니다!")
            with c_go2:
                if st.button("⬅️ 2단계 설계도 보기", use_container_width=True):
                    st.session_state["t2_step"] = 2
                    st.rerun()
            with c_go3:
                if st.button("✨ 새로운 주제로 새 글 작성", type="secondary", use_container_width=True):
                    st.session_state["t2_step"] = 1
                    st.session_state["t2_topic"] = ""
                    st.session_state["t2_direction"] = ""
                    st.session_state["t2_seeds"] = []
                    st.session_state["t2_blueprint"] = None
                    st.session_state["t2_synthesis_done"] = False
                    st.session_state["active_creation_id"] = None
                    st.session_state["t2_input_topic"] = ""
                    st.session_state["t2_input_direction"] = ""
                    st.rerun()

# -------------------------------------------------------------
# TAB 3: Seed 이미지 뷰어 & 마크다운 에디터 (Studio View)
# -------------------------------------------------------------
with tabs[2]:
    t3_c1, t3_c2 = st.columns([3, 1])
    with t3_c1:
        st.header("3. Seed 원본 이미지 뷰어 & 마크다운 퇴고 스튜디오")
    with t3_c2:
        st.info(f"🔍 퇴고 AI: `{proof_llm.model}` ({proof_llm.thinking_level.upper()})")

    all_creations = repo.list_creations(limit=30)
    creation_options = {}
    if st.session_state.get("t2_topic"):
        t2_snippet = st.session_state["t2_topic"][:28] + ("..." if len(st.session_state["t2_topic"]) > 28 else "")
        creation_options["_live_t2_draft"] = f"✨ [2번 탭 기획 주제] {t2_snippet}"
    for c in all_creations:
        creation_options[c["creation_id"]] = f"[{c['status']}] {c['topic']} ({c['creation_id']})"

    col_select1, col_select2 = st.columns([6, 4])
    with col_select1:
        if creation_options:
            c_keys = list(creation_options.keys())
            active_id = st.session_state.get("active_creation_id")
            default_index = c_keys.index(active_id) if active_id in c_keys else 0
            selected_cid = st.selectbox(
                "편집할 초안 / 결과물 선택",
                options=c_keys,
                index=default_index,
                format_func=lambda cid: creation_options.get(cid, cid),
                key=f"tab3_select_cid_{active_id or 'none'}",
            )
        else:
            selected_cid = None
            st.info("아직 생성된 초안이 없습니다. 2번 탭에서 초안을 생성하거나 아래에서 Seed 문서를 직접 선택해 이미지를 탐색하세요.")

    with col_select2:
        all_doc_options = {a.doc_id: f"Seed #{a.doc_id}: {a.title}" for a in repo.list_articles()}
        standalone_seed = st.selectbox(
            "또는 특정 Seed 아티클 이미지 직접 둘러보기",
            options=["(초안 연동)"] + list(all_doc_options.keys()),
            format_func=lambda did: all_doc_options.get(did, did),
        )

    # Determine which seeds to display in visual gallery
    seed_ids_to_show = []
    if standalone_seed != "(초안 연동)":
        seed_ids_to_show = [standalone_seed]
    elif selected_cid and selected_cid != "_live_t2_draft":
        creation_data = repo.get_creation(selected_cid)
        if creation_data:
            seed_ids_to_show = creation_data.get("seed_doc_ids", [])
    elif selected_cid == "_live_t2_draft":
        t2_seeds = st.session_state.get("t2_seeds") or []
        seed_ids_to_show = [s.doc_id for s in t2_seeds if hasattr(s, "doc_id")]
        if not seed_ids_to_show:
            seed_ids_to_show = [a.doc_id for a in repo.list_articles()[:2]]
    else:
        # Default fallback to first 2 articles if no draft yet
        seed_ids_to_show = [a.doc_id for a in repo.list_articles()[:2]]

    col_left, col_right = st.columns([5, 7])

    # Left Pane: Seed Image Gallery & Materials
    with col_left:
        st.subheader("🖼️ Seed 시각 자료 갤러리")
        st.caption("썸네일을 확인하고 [🔍 크게 보기]를 클릭하면 라이트박스 모달로 원본을 확인할 수 있습니다.")

        has_images = False
        for s_id in seed_ids_to_show:
            assets = repo.get_visual_assets(s_id)
            s_art = repo.get_article(s_id)
            s_title = s_art.title if s_art else s_id
            
            with st.expander(f"📁 Seed #{s_id}: {s_title} (이미지 {len(assets)}개)", expanded=True):
                if assets:
                    has_images = True
                    # Grid of thumbnails (2 columns)
                    for i in range(0, len(assets), 2):
                        row_cols = st.columns(2)
                        for j in range(2):
                            idx = i + j
                            if idx < len(assets):
                                a = assets[idx]
                                real_path = resolve_asset_path(a.file_path)
                                with row_cols[j]:
                                    if real_path and real_path.exists():
                                        st.image(str(real_path), use_container_width=True)
                                        st.caption(f"**{a.asset_id}** (p.{a.page_no})")
                                        if a.caption:
                                            short_cap = a.caption[:30] + "..." if len(a.caption) > 30 else a.caption
                                            st.write(f"_{short_cap}_")
                                        if st.button("🔍 크게 보기", key=f"zoom_{s_id}_{a.asset_id}_{idx}", use_container_width=True):
                                            show_lightbox_dialog(str(real_path), a.asset_id, s_id, a.page_no, a.caption, s_title)
                                    else:
                                        st.warning(f"이미지 누락: {a.file_path}")
                else:
                    st.caption("이 문서에는 추출된 이미지가 없습니다.")

        if not has_images:
            st.info("선별된 문서에 추출된 이미지가 없습니다.")

    # Right Pane: Editor & Finalize
    with col_right:
        st.subheader("✍️ 마크다운 에디터 & 실시간 미리보기")
        
        # Load active text
        creation = None
        cur_topic = ""
        cur_direction = ""
        cur_blueprint = None

        current_loaded = st.session_state.get("_loaded_cid")
        if selected_cid and selected_cid != "_live_t2_draft":
            creation = repo.get_creation(selected_cid)
            if creation:
                cur_topic = creation.get("topic", "")
                cur_direction = creation.get("direction", "")
                bp_raw = creation.get("blueprint_json", "")
                if bp_raw:
                    try:
                        cur_blueprint = json.loads(bp_raw)
                    except Exception:
                        pass
                if current_loaded != selected_cid:
                    st.session_state["_loaded_cid"] = selected_cid
                    active_content = creation["user_final_text"] if creation["user_final_text"] else creation["ai_draft_text"]
                    frontmatter, clean_body = ArticleProofreader.split_frontmatter(active_content)
                    st.session_state["editor_frontmatter"] = frontmatter
                    st.session_state["editor_text"] = clean_body
                    st.session_state["notes_text"] = creation.get("custom_notes", "")
                    st.session_state[f"editor_area_{selected_cid}"] = clean_body
                    st.session_state[f"editor_area_side_{selected_cid}"] = clean_body
        else:
            cur_topic = st.session_state.get("t2_topic", "")
            cur_direction = st.session_state.get("t2_direction", "")
            cur_blueprint = st.session_state.get("t2_blueprint")
            if current_loaded != "_live_t2_draft":
                st.session_state["_loaded_cid"] = "_live_t2_draft"
                live_text = st.session_state.get("live_draft_text")
                if not live_text:
                    live_text = f"# {cur_topic}\n\n> 💡 **집필 의도**: {cur_direction}\n\n## 1. 들어가며\n\n여기에 본문 내용을 작성해 보세요."
                st.session_state["editor_text"] = live_text
                st.session_state["editor_frontmatter"] = f"---\ntopic: {json.dumps(cur_topic, ensure_ascii=False)}\ndirection: {json.dumps(cur_direction, ensure_ascii=False)}\nstatus: DRAFT\n---"
                st.session_state["editor_area__live_t2_draft"] = live_text
                st.session_state["editor_area_side__live_t2_draft"] = live_text

        # Safety: If editor_text currently has frontmatter in session state, split it automatically
        if (st.session_state.get("editor_text") or "").startswith("---"):
            fm, cb = ArticleProofreader.split_frontmatter(st.session_state["editor_text"])
            if fm:
                st.session_state["editor_frontmatter"] = fm
                st.session_state["editor_text"] = cb
                st.session_state[f"editor_area_{selected_cid or 'default'}"] = cb
                st.session_state[f"editor_area_side_{selected_cid or 'default'}"] = cb

        # Prominently Display Planning Brief (Topic, Context & Blueprint)
        if cur_topic or cur_direction:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: rgba(30, 136, 229, 0.08); border-left: 4px solid #1E88E5; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px;">
                        <div style="font-size: 13px; font-weight: 700; color: #1565C0; margin-bottom: 4px;">🎯 타깃 주제 (Topic)</div>
                        <div style="font-size: 15px; font-weight: 600; color: #111; margin-bottom: 8px;">{cur_topic or '미지정'}</div>
                        <div style="font-size: 12px; font-weight: 700; color: #555; margin-bottom: 4px;">🧭 집필 방향 및 내 고유 관점 (Context)</div>
                        <div style="font-size: 13px; color: #333; line-height: 1.5; white-space: pre-wrap;">{cur_direction or '미지정'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if cur_blueprint:
                bp_title = cur_blueprint.get("proposed_title") if isinstance(cur_blueprint, dict) else getattr(cur_blueprint, "proposed_title", "")
                bp_reframing = cur_blueprint.get("synthesized_reframing") if isinstance(cur_blueprint, dict) else getattr(cur_blueprint, "synthesized_reframing", "")
                outline = cur_blueprint.get("section_outline", []) if isinstance(cur_blueprint, dict) else getattr(cur_blueprint, "section_outline", [])
                with st.expander(f"🗺️ AI 융합 설계도 요약 (제안 제목: {bp_title})", expanded=False):
                    if bp_reframing:
                        st.markdown(f"**융합 관점 전환:** {bp_reframing}")
                    if outline:
                        st.markdown("**목차 아웃라인:**")
                        for sec in outline:
                            st.write(f"- {sec}")

        # Metadata Raw YAML (Collapsible for verification)
        if st.session_state.get("editor_frontmatter"):
            with st.expander("📌 원본 YAML 프론트매터 메타데이터 (발행 시 자동 보존)", expanded=False):
                st.code(st.session_state["editor_frontmatter"], language="yaml")

        edit_mode = st.radio("보기 모드", ["에디터 (수정)", "실시간 미리보기", "나란히 보기"], horizontal=True)

        if edit_mode == "에디터 (수정)":
            edited_val = st.text_area(
                "본문 마크다운 내용 (순수 본문 | # 제목부터 작성)",
                value=st.session_state.get("editor_text", ""),
                height=520,
                key=f"editor_area_{selected_cid or 'default'}",
                placeholder="2번 탭에서 초안을 생성하거나, 여기에 직접 새로운 글을 작성해 보세요.",
            )
            st.session_state["editor_text"] = edited_val
            if selected_cid == "_live_t2_draft":
                st.session_state["live_draft_text"] = edited_val
        elif edit_mode == "실시간 미리보기":
            if st.session_state.get("editor_text"):
                st.markdown(st.session_state["editor_text"])
            else:
                st.info("작성된 내용이 없습니다.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                edited_val = st.text_area(
                    "본문 수정 (순수 본문)",
                    value=st.session_state.get("editor_text", ""),
                    height=520,
                    key=f"editor_area_side_{selected_cid or 'default'}",
                )
                st.session_state["editor_text"] = edited_val
                if selected_cid == "_live_t2_draft":
                    st.session_state["live_draft_text"] = edited_val
            with c2:
                if st.session_state.get("editor_text"):
                    st.markdown(st.session_state["editor_text"])
                else:
                    st.info("미리보기 내용이 없습니다.")

        # AI Proofreader & Multi-Platform Critique Copilot
        st.divider()
        with st.expander("✨ AI 수석 편집장의 매체별 첨삭 & 퇴고 코치 (Editorial Copilot)", expanded=True):
            st.markdown(
                "작성 중인 본문을 정밀 진단하여 **브런치스토리**, **링크드인**, **스레드** 등 목표 매체에서 "
                "**'읽히는 글', '팔리는 글'**이 되도록 매체 최적화 첨삭 및 전면 개정본을 제안합니다."
            )

            p_col1, p_col2 = st.columns([1, 1])
            with p_col1:
                target_platform = st.selectbox(
                    "목표 발행 매체 (플랫폼 최적화)",
                    options=["brunch", "linkedin", "threads", "general"],
                    format_func=lambda x: {
                        "brunch": "☕ 브런치스토리 (Brunch - 서사/감성 에세이)",
                        "linkedin": "💼 링크드인 (LinkedIn - 3초 훅/비즈니스 레슨런)",
                        "threads": "📱 스레드 (Threads - 모바일 단문/호흡/댓글유도)",
                        "general": "🎯 종합 실무/밸런스 (논리 전개/문장 다이어트)",
                    }[x],
                    index=0,
                )
            with p_col2:
                review_mode = st.selectbox(
                    "첨삭 모드",
                    options=["rewrite", "report", "custom"],
                    format_func=lambda x: {
                        "rewrite": "🪄 매체 맞춤 개정본 + 진단 리포트 (추천)",
                        "report": "📊 종합 진단 리포트만 보기",
                        "custom": "💬 사용자 맞춤 지시 첨삭",
                    }[x],
                    index=0,
                )

            custom_prompt_input = ""
            if review_mode == "custom":
                custom_prompt_input = st.text_input(
                    "편집장에게 전달할 특별 지시사항",
                    placeholder="예: 조금 더 도발적인 질문으로 시작하고, 개발자나 디자이너의 예시를 하나씩 추가해 줘.",
                )

            proofread_btn = st.button("🚀 AI 수석 편집장에게 첨삭 요청하기", use_container_width=True)

            proof_state_key = f"proof_result_{selected_cid or 'default'}"
            if proofread_btn:
                current_text = st.session_state.get("editor_text", "").strip()
                if not current_text:
                    st.warning("첨삭할 본문 내용이 없습니다. 먼저 초안을 작성하거나 불러와 주세요.")
                else:
                    with st.spinner("AI 수석 편집장이 훅킹 파워, 전개 밸런스, 매체 문체 핏을 분석 중입니다..."):
                        res = proofreader.review_sync(
                            content=current_text,
                            platform=target_platform,
                            mode=review_mode,
                            custom_instruction=custom_prompt_input,
                            metadata_context=st.session_state.get("editor_frontmatter", ""),
                        )
                        st.session_state[proof_state_key] = res
                        st.success("첨삭 진단 및 제안 생성이 완료되었습니다!")

            # Display review result if available in session state
            if proof_state_key in st.session_state and st.session_state[proof_state_key]:
                r = st.session_state[proof_state_key]
                st.markdown("---")

                # Metric Cards
                m_c1, m_c2, m_c3 = st.columns(3)
                with m_c1:
                    st.metric("🎣 3초 후킹 점수", f"{r.get('hooking_score', 8)} / 10")
                with m_c2:
                    st.metric("⚖️ 내용 전개 밸런스", f"{r.get('balance_score', 8)} / 10")
                with m_c3:
                    st.metric("🎯 매체 적합도", f"{r.get('platform_score', 8)} / 10")

                st.markdown(r.get("critique_report", ""))

                # Section for applying critique feedback to generate rewrite
                st.markdown("---")
                st.markdown("#### 🪄 진단 리포트 피드백 기반 자동 퇴고 (Refinement)")
                st.caption("위 종합 진단 리포트의 킬러 포인트와 개선 권고사항을 본문에 즉시 반영하여 새로운 매체 맞춤 개정본을 생성합니다.")

                col_refine_input, col_refine_act = st.columns([7, 3])
                with col_refine_input:
                    extra_feedback_input = st.text_input(
                        "✍️ 추가 반영 요청사항 (선택사항)",
                        placeholder="예: 도입부 훅을 더 강하게 하고, 300명 회원수첩 일화의 비용 참사를 더 부각해 줘.",
                        key=f"extra_refine_{selected_cid or 'default'}",
                    )
                with col_refine_act:
                    st.write("")
                    refine_btn = st.button(
                        "✨ [위 진단 피드백 반영 개정본 생성]",
                        type="primary",
                        use_container_width=True,
                        key=f"apply_critique_btn_{selected_cid or 'default'}",
                    )

                if refine_btn:
                    with st.spinner("진단 리포트 피드백을 본문에 반영하여 개정본을 집필 중입니다..."):
                        combined_critique = r.get("critique_report", "")
                        if extra_feedback_input.strip():
                            combined_critique += f"\n\n[사용자 추가 지시사항]:\n{extra_feedback_input.strip()}"

                        rewrite_res = proofreader.review_sync(
                            content=st.session_state.get("editor_text", "").strip(),
                            platform=target_platform,
                            mode="rewrite",
                            critique_feedback=combined_critique,
                            metadata_context=st.session_state.get("editor_frontmatter", ""),
                        )
                        r["rewritten_text"] = rewrite_res.get("rewritten_text")
                        st.session_state[proof_state_key] = r
                        st.success("🎉 진단 피드백을 반영한 개정본 생성이 완료되었습니다! 아래에서 확인하고 본문에 적용하세요.")
                        st.rerun()

                # If rewrite is generated, show preview and one-click apply button
                if r.get("rewritten_text"):
                    st.markdown("#### 📝 매체 맞춤 개정본 (AI 피드백 반영)")
                    rewritten_content = r["rewritten_text"]

                    diff_tab1, diff_tab2 = st.tabs(["🪄 개정본 미리보기", "⚖️ 현재 내 본문과 비교"])
                    with diff_tab1:
                        st.text_area(
                            "개정본 본문",
                            value=rewritten_content,
                            height=320,
                            key=f"preview_box_{selected_cid or 'default'}",
                        )
                    with diff_tab2:
                        col_comp1, col_comp2 = st.columns(2)
                        with col_comp1:
                            st.caption("**[현재 본문]**")
                            st.text_area("현재 본문", value=st.session_state.get("editor_text", ""), height=300, disabled=True, key=f"orig_cmp_{selected_cid or 'default'}")
                        with col_comp2:
                            st.caption("**[AI 개정본]**")
                            st.text_area("AI 개정본", value=rewritten_content, height=300, disabled=True, key=f"rewr_cmp_{selected_cid or 'default'}")

                    col_apply, _ = st.columns([3, 1])
                    with col_apply:
                        if st.button("📥 [👉 이 개정본을 에디터 본문에 즉시 반영하기]", type="primary", use_container_width=True):
                            st.session_state["editor_text"] = rewritten_content
                            st.session_state[f"editor_area_{selected_cid or 'default'}"] = rewritten_content
                            st.session_state[f"editor_area_side_{selected_cid or 'default'}"] = rewritten_content
                            st.success("에디터에 첨삭본이 즉시 반영되었습니다! 추가 수정 후 언제든 다시 첨삭받거나 확정 저장하세요.")
                            st.rerun()

        st.divider()

        st.session_state["notes_text"] = st.text_input(
            "사용자 수정 메모 / 의도 (향후 스타일 학습 시 참고)",
            value=st.session_state["notes_text"],
            placeholder="예: 단문 종결어미 통일, AI 상투적 박스 삭제, Seed 이미지 삽입",
        )

        col_save1, col_save2 = st.columns([3, 2])
        with col_save1:
            save_disabled = not bool(st.session_state["editor_text"].strip())
            if st.button("💾 [나의 결과물로 확정 저장 (Save to My Corpus)]", type="primary", use_container_width=True, disabled=save_disabled):
                final_body = st.session_state["editor_text"].strip()
                notes = st.session_state["notes_text"]
                frontmatter = st.session_state.get("editor_frontmatter", "").strip()
                if frontmatter:
                    final_full_text = f"{frontmatter}\n\n{final_body}"
                else:
                    final_full_text = final_body

                target_id = selected_cid
                if not target_id or target_id == "_live_t2_draft":
                    # Create a new creation entry if saved without generator
                    import datetime
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    target_id = f"cr_{now_str}"
                    repo.save_draft_creation(
                        creation_id=target_id,
                        topic=cur_topic or "직접 작성한 새 글",
                        direction=cur_direction or "",
                        target_archetype="custom",
                        seed_doc_ids=seed_ids_to_show,
                        blueprint_json="{}",
                        distilled_sheets_json="[]",
                        ai_draft_text=final_full_text,
                        status="DRAFT",
                    )

                repo.update_creation_final(
                    creation_id=target_id,
                    user_final_text=final_full_text,
                    custom_notes=notes,
                    status="FINALIZED",
                )
                saved_path = style_learner.save_finalized_article(
                    creation_id=target_id,
                    title="나의_글",
                    content=final_full_text,
                )
                st.success(f"🎉 결과물이 확정 저장되었습니다! (ID: {target_id}, 파일: {saved_path.name})")
                st.rerun()

        with col_save2:
            if selected_cid and selected_cid != "_live_t2_draft" and creation:
                current_status = creation["status"]
                st.metric("현재 문서 상태", current_status)
            else:
                st.caption("신규 작성 모드")

# -------------------------------------------------------------
# TAB 4: 나의 결과물 & 스타일 학습소 (My Corpus & Style Learning)
# -------------------------------------------------------------
with tabs[3]:
    st.header("4. 나의 결과물 저장소 & Diff 기반 스타일 학습 루프")

    finalized_list = repo.list_creations(status="FINALIZED")
    finalized_count = len(finalized_list)

    # Maturity Gauge
    st.subheader("📈 나만의 문체 스타일 학습 성숙도 게이지")
    progress_val = min(finalized_count / 5.0, 1.0)
    st.progress(progress_val)
    st.markdown(
        f"**누적 확정 결과물:** `{finalized_count} / 5 편` "
        f"{'🎉 (스타일 학습 권장 기준 5편 달성!)' if finalized_count >= 5 else f'(5편까지 {5 - finalized_count}편 남음)'}"
    )

    if finalized_count == 0:
        st.info(
            "🌱 **나만의 글쓰기 스타일 학습 준비 중**\n\n"
            "사용자님의 고유한 문체를 학습하기 위해, 3번 탭(Seed 스튜디오)에서 글을 작성·퇴고하여 "
            "**[나의 결과물로 확정 저장]**을 1편씩 쌓아주세요.\n\n"
            "5편 이상 누적되면 AI가 원본 초안과 사용자님의 최종본 간의 Diff(문장 길이, 종결어미, 삭제 패턴 등)를 "
            "정밀 분석하여 나만의 고유 스타일 프로필(`style_profile.json`)을 자동으로 추출합니다."
        )
    else:
        col_btn1, col_btn2 = st.columns([3, 4])
        with col_btn1:
            force_learning = st.checkbox("5편 미만이어도 강제 학습 진행", value=(finalized_count > 0 and finalized_count < 5))
            learn_btn = st.button("🎯 나만의 문체 스타일 추출/갱신하기", type="primary", use_container_width=True)

        if learn_btn:
            with st.spinner("AI 초안과 사용자 수정본의 Diff 쌍을 분석하여 스타일 프로필 추출 중..."):
                try:
                    learned_profile = style_learner.learn_style_sync(min_count=5, force=force_learning)
                    if learned_profile:
                        st.success(f"축하합니다! 나만의 스타일 프로필(v{learned_profile.profile_version}) 추출이 완료되었습니다.")
                        st.rerun()
                    else:
                        st.warning("스타일 학습을 위한 확정된 결과물이 부족합니다. 초안을 수정한 뒤 [나의 결과물로 확정 저장]을 완료해주세요.")
                except Exception as e:
                    st.error(f"⚠️ 스타일 프로필 추출 중 오류가 발생했습니다: {e}")
                    st.info("💡 Google Gemini API 서버가 일시적인 고부하(503) 상태일 수 있습니다. 잠시 후 [나만의 문체 스타일 추출/갱신하기] 버튼을 다시 눌러주세요.")

    # Display active style profile if exists
    active_prof = style_learner.get_active_profile()
    if active_prof:
        st.divider()
        st.subheader(f"✨ 현재 활성화된 나만의 스타일 프로필 (v{active_prof.profile_version})")
        st.caption(f"기반 결과물 편수: {active_prof.based_on_creation_count}편 | 저장 위치: `data/my_corpus/style_profile.json`")

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown("#### 🗣️ 선호 어조 및 종결어미")
            for item in active_prof.preferred_tone_and_endings:
                st.write(f"- {item}")

            st.markdown("#### 📐 구조 및 단락 전개 선호")
            for item in active_prof.structural_preferences:
                st.write(f"- {item}")

        with p_col2:
            st.markdown("#### 🚫 기피/삭제 패턴 (Forbidden Patterns)")
            for item in active_prof.forbidden_patterns:
                st.write(f"- ❌ {item}")

            st.markdown("#### 🖋️ 시그니처 포맷팅 규칙")
            for item in active_prof.signature_formatting_rules:
                st.write(f"- 📌 {item}")

    # Diff View of Finalized Articles
    st.divider()
    st.subheader("📚 확정된 나의 결과물 & Diff 비교 아카이브")
    if finalized_list:
        for idx, item in enumerate(finalized_list):
            title = item["topic"]
            cid = item["creation_id"]
            used_badge = "✅ 스타일 학습 반영됨" if item["used_for_style_learning"] else "⏳ 학습 대기 중"
            with st.expander(f"{idx + 1}. {title} ({cid}) - {used_badge}"):
                st.caption(f"작성 일시: {item['created_at']} | 확정 일시: {item.get('finalized_at', '-')}")
                if item.get("custom_notes"):
                    st.info(f"사용자 퇴고 노트: {item['custom_notes']}")
                
                diff_col1, diff_col2 = st.columns(2)
                with diff_col1:
                    st.markdown("**[Before: AI 생성 원본 초안]**")
                    st.text_area(f"ai_draft_{cid}", value=item["ai_draft_text"], height=300, disabled=True)
                with diff_col2:
                    st.markdown("**[After: 사용자 확정 최종본]**")
                    st.text_area(f"user_final_{cid}", value=item["user_final_text"], height=300, disabled=True)
    else:
        st.info("아직 확정된 나의 결과물이 없습니다. 3번째 탭에서 초안을 수정하고 확정 저장해 보세요.")
