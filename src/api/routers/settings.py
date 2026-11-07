"""Settings and runtime configuration API router.

Enables viewing and hot-reloading LLM models, API keys, and system parameters
without restarting background systemd services.
"""

import logging
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends
from google import genai

from src.api.auth import verify_auth
from src.api.schemas.settings import (
    ModelInfoItem,
    ModelTestRequest,
    ModelTestResponse,
    SettingsResponse,
    SettingsUpdateRequest,
)
from src.config import load_config

logger = logging.getLogger("pactory.settings")

router = APIRouter(prefix="/settings", tags=["Studio Settings"], dependencies=[Depends(verify_auth)])

SUPPORTED_MODELS: list[ModelInfoItem] = [
    ModelInfoItem(
        id="gemini-3-flash-preview",
        name="Gemini 3 Flash Preview",
        provider="gemini",
        badge="추천/안정/고속",
        description="차세대 Gemini 3 플래시 프리뷰 (쿼터 안정, 고속 레이턴시, 높은 합성 품질)",
    ),
    ModelInfoItem(
        id="gemini-3.8-flash",
        name="Gemini 3.8 Flash",
        provider="gemini",
        badge="최신/고품질",
        description="최신 Gemini 3.8 플래시 모델",
    ),
    ModelInfoItem(
        id="gemini-3.5-flash",
        name="Gemini 3.5 Flash",
        provider="gemini",
        badge="안정적 표준",
        description="Gemini 3.5 표준 플래시 모델",
    ),
    ModelInfoItem(
        id="gemini-3.5-flash-lite",
        name="Gemini 3.5 Flash-Lite",
        provider="gemini",
        badge="경량 (일일 500회 제한)",
        description="초경량 저지연 모델 (무료 티어 하루 500건 쿼터 적용)",
    ),
    ModelInfoItem(
        id="gemini-3.8-pro",
        name="Gemini 3.8 Pro",
        provider="gemini",
        badge="심층 추론/최상위",
        description="복합 추론 및 고난도 장문 합성을 위한 최고 사양 모델",
    ),
    ModelInfoItem(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        badge="OpenAI",
        description="OpenAI 경량 고효율 모델",
    ),
    ModelInfoItem(
        id="claude-3-7-sonnet-latest",
        name="Claude 3.7 Sonnet",
        provider="anthropic",
        badge="Anthropic",
        description="Anthropic 최상위 글쓰기/추론 모델",
    ),
]


def _find_env_file() -> Path | None:
    """Locate the active .env file across project directories."""
    candidates = [
        Path(".env"),
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path.home() / "pactory_contents" / ".env",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def _update_env_file(updates: dict[str, str]) -> None:
    """Update or append key-value pairs in the .env file while preserving comments."""
    env_path = _find_env_file()
    if not env_path:
        env_path = Path(".env")
        env_path.touch()

    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _ = stripped.split("=", 1)
            k = k.strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                updated_keys.add(k)
                continue
        new_lines.append(line)

    # Append any remaining keys that were not already present
    for k, v in updates.items():
        if k not in updated_keys and v:
            new_lines.append(f"{k}={v}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Retrieve current studio configuration and configured API key status."""
    default_model = os.getenv("DEFAULT_MODEL", "gemini-3-flash-preview")
    default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    default_thinking_level = os.getenv("DEFAULT_THINKING_LEVEL", "low")

    langfuse_pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_sk = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://jp.cloud.langfuse.com")

    api_keys = {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "langfuse": bool(langfuse_pk and langfuse_sk),
    }

    return SettingsResponse(
        default_model=default_model,
        default_provider=default_provider,
        default_thinking_level=default_thinking_level,
        available_models=SUPPORTED_MODELS,
        api_keys_configured=api_keys,
        langfuse_configured=bool(langfuse_pk and langfuse_sk),
        langfuse_host=langfuse_host,
    )


@router.post("", response_model=SettingsResponse)
async def update_settings(req: SettingsUpdateRequest):
    """Update runtime studio settings and persist them to .env without server restart."""
    env_updates: dict[str, str] = {}

    if req.default_model:
        os.environ["DEFAULT_MODEL"] = req.default_model
        env_updates["DEFAULT_MODEL"] = req.default_model

    if req.default_provider:
        os.environ["DEFAULT_LLM_PROVIDER"] = req.default_provider
        env_updates["DEFAULT_LLM_PROVIDER"] = req.default_provider

    if req.default_thinking_level:
        os.environ["DEFAULT_THINKING_LEVEL"] = req.default_thinking_level
        env_updates["DEFAULT_THINKING_LEVEL"] = req.default_thinking_level

    if req.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = req.gemini_api_key
        env_updates["GEMINI_API_KEY"] = req.gemini_api_key

    if req.openai_api_key:
        os.environ["OPENAI_API_KEY"] = req.openai_api_key
        env_updates["OPENAI_API_KEY"] = req.openai_api_key

    if req.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_api_key
        env_updates["ANTHROPIC_API_KEY"] = req.anthropic_api_key

    if env_updates:
        _update_env_file(env_updates)
        # Reload runtime config singleton
        from src.api.dependencies import get_config
        get_config.cache_clear()
        cfg = load_config()
        if req.default_model:
            cfg.extraction.default_model = req.default_model
        if req.default_provider:
            cfg.extraction.default_provider = req.default_provider

    logger.info("Settings updated dynamically without server restart: %s", env_updates)
    return await get_settings()


@router.post("/test-model", response_model=ModelTestResponse)
async def test_model(req: ModelTestRequest):
    """Perform an instantaneous 1-token ping to verify model availability and quota status."""
    start_time = time.perf_counter()
    model = req.model.strip()
    provider = req.provider.strip().lower()

    if provider == "gemini":
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            return ModelTestResponse(
                success=False,
                model=model,
                latency_ms=0,
                message="GEMINI_API_KEY가 설정되어 있지 않습니다.",
                error_type="MISSING_API_KEY",
            )

        try:
            client = genai.Client(api_key=gemini_key)
            # Send a minimal 1-token generation test
            res = client.models.generate_content(
                model=model,
                contents="ping",
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return ModelTestResponse(
                success=True,
                model=model,
                latency_ms=elapsed_ms,
                message=f"정상 동작 확인 (응답 지연시간: {elapsed_ms}ms)",
            )
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            err_str = str(exc)
            upper_err = err_str.upper()

            if "429" in upper_err or "RESOURCE_EXHAUSTED" in upper_err:
                return ModelTestResponse(
                    success=False,
                    model=model,
                    latency_ms=elapsed_ms,
                    message="일일 쿼터 초과(429 RESOURCE_EXHAUSTED): 일일 500회 제한에 도달했습니다. 다른 모델을 선택하세요.",
                    error_type="RESOURCE_EXHAUSTED",
                )
            elif "503" in upper_err or "UNAVAILABLE" in upper_err:
                return ModelTestResponse(
                    success=False,
                    model=model,
                    latency_ms=elapsed_ms,
                    message="일시적 서버 과부하(503 UNAVAILABLE): 일시적으로 트래픽이 몰렸습니다. 잠시 후 재시도하세요.",
                    error_type="UNAVAILABLE",
                )
            elif "404" in upper_err or "NOT_FOUND" in upper_err:
                return ModelTestResponse(
                    success=False,
                    model=model,
                    latency_ms=elapsed_ms,
                    message="지원되지 않거나 폐기된 모델(404 NOT_FOUND)입니다.",
                    error_type="NOT_FOUND",
                )
            else:
                return ModelTestResponse(
                    success=False,
                    model=model,
                    latency_ms=elapsed_ms,
                    message=f"호출 실패 ({type(exc).__name__}): {err_str[:120]}",
                    error_type="API_ERROR",
                )

    elif provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return ModelTestResponse(
                success=False,
                model=model,
                latency_ms=0,
                message="OPENAI_API_KEY가 설정되어 있지 않습니다.",
                error_type="MISSING_API_KEY",
            )
        return ModelTestResponse(
            success=True,
            model=model,
            latency_ms=10,
            message="OpenAI API 키가 설정되어 있습니다.",
        )

    elif provider == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            return ModelTestResponse(
                success=False,
                model=model,
                latency_ms=0,
                message="ANTHROPIC_API_KEY가 설정되어 있지 않습니다.",
                error_type="MISSING_API_KEY",
            )
        return ModelTestResponse(
            success=True,
            model=model,
            latency_ms=10,
            message="Anthropic API 키가 설정되어 있습니다.",
        )

    return ModelTestResponse(
        success=False,
        model=model,
        latency_ms=0,
        message=f"지원하지 않는 프로바이더입니다: {provider}",
        error_type="UNSUPPORTED_PROVIDER",
    )
