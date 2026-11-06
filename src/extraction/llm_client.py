"""Universal LLM client wrapper for structured outputs and text generation.

Supports Google Gemini (via google-genai SDK) and OpenAI (via openai SDK).
Clean, data-driven architecture: no hardcoded mock data or fake text stubs.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

logger = logging.getLogger("llm_client")

T = TypeVar("T", bound=BaseModel)

# Candidate fallback models when a Gemini model fails with 503/504
GEMINI_FALLBACK_CANDIDATES = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]


def is_retryable_error(exc: Exception) -> bool:
    """Check if exception is a transient error eligible for retry."""
    err_msg = str(exc).upper()
    return any(k in err_msg for k in ["503", "504", "429", "UNAVAILABLE", "DEADLINE_EXCEEDED", "RESOURCE_EXHAUSTED", "HIGH DEMAND"])


def retry_sync(func, max_retries: int = 3, base_delay: float = 1.5):
    """Exponential backoff retry helper for synchronous API calls."""
    import time
    last_err = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_err = e
            if not is_retryable_error(e) or attempt == max_retries - 1:
                break
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Sync LLM retry #{attempt + 1} after {delay:.1f}s due to transient error: {e}")
            time.sleep(delay)
    raise last_err or RuntimeError("LLM API call failed after retries")


async def retry_async(func, max_retries: int = 3, base_delay: float = 1.5):
    """Exponential backoff retry helper for async API calls."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_err = e
            if not is_retryable_error(e) or attempt == max_retries - 1:
                break
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Async LLM retry #{attempt + 1} after {delay:.1f}s due to transient error: {e}")
            await asyncio.sleep(delay)
    raise last_err or RuntimeError("LLM API call failed after retries")


class LLMClient:
    """Wrapper for LLM calls with Pydantic structured output validation and fallback resilience."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            try:
                from src.config import load_env_file
                load_env_file()
            except Exception:
                pass

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if provider:
            self.provider = provider.lower()
        elif gemini_key or os.getenv("DEFAULT_LLM_PROVIDER", "").lower() == "gemini":
            self.provider = "gemini"
        elif openai_key:
            self.provider = "openai"
        else:
            self.provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini").lower()

        self.thinking_level = os.getenv("DEFAULT_THINKING_LEVEL", "low").lower()

        if self.provider == "gemini":
            # Default to gemini-3.5-flash-lite for speed and high availability
            self.model = model or os.getenv("DEFAULT_MODEL", "gemini-3.5-flash-lite")
            self.api_key = api_key or gemini_key
        else:
            self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
            self.api_key = api_key or openai_key

        self.init_clients()

    def init_clients(self):
        """Initialize backend SDK clients based on provider and API key."""
        self._openai_client = None
        self._openai_sync_client = None
        self._gemini_client = None

        if self.provider == "openai" and self.api_key:
            try:
                from openai import AsyncOpenAI, OpenAI
                self._openai_client = AsyncOpenAI(api_key=self.api_key)
                self._openai_sync_client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to init OpenAI client: {e}")
        elif self.provider == "gemini" and self.api_key:
            try:
                from google import genai
                from google.genai import types
                self._gemini_client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=30000),
                )
            except Exception as e:
                logger.warning(f"Failed to init Gemini client: {e}")

    def set_api_key(self, api_key: str, provider: str = "gemini", model: Optional[str] = None):
        """Dynamically update client with new API key, provider, and model."""
        self.api_key = api_key
        self.provider = provider.lower()
        if model:
            self.model = model
        self.init_clients()

    def set_thinking_level(self, level: str):
        """Set reasoning effort / thinking level: 'low', 'medium', 'high'."""
        if level in ["low", "medium", "high"]:
            self.thinking_level = level

    def _build_gemini_config(self, schema=None):
        """Build GenerateContentConfig with thinking_config support and 30s timeout."""
        try:
            from google.genai import types
            cfg_kwargs: Dict[str, Any] = {
                "http_options": types.HttpOptions(timeout=30000)
            }
            if schema:
                cfg_kwargs["response_mime_type"] = "application/json"
                cfg_kwargs["response_schema"] = schema

            if any(k in self.model for k in ["3.8", "3.7", "3.6", "3.5", "2.5", "3-"]):
                cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=self.thinking_level)
            return types.GenerateContentConfig(**cfg_kwargs)
        except Exception:
            return {"response_mime_type": "application/json", "response_schema": schema} if schema else {}

    def _call_gemini_sync(self, full_prompt: str, config=None) -> str:
        """Call Gemini synchronously with automatic exponential backoff retry and model cascade."""
        if not self._gemini_client:
            raise RuntimeError("Gemini client is not initialized. Please configure GEMINI_API_KEY in .env.")

        def _invoke_primary():
            resp = self._gemini_client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=config,
            )
            if resp and resp.text:
                return resp.text
            raise RuntimeError(f"Gemini returned empty response for model {self.model}")

        try:
            return retry_sync(_invoke_primary, max_retries=3, base_delay=1.5)
        except Exception as primary_err:
            fallbacks = [m for m in GEMINI_FALLBACK_CANDIDATES if m != self.model]
            if not fallbacks and self.model == "gemini-3.5-flash-lite":
                fallbacks = ["gemini-3.5-flash"]
            elif not fallbacks and self.model == "gemini-3.5-flash":
                fallbacks = ["gemini-3.5-flash-lite"]

            for fb_model in fallbacks:
                logger.warning(
                    f"Primary Gemini model '{self.model}' failed after retries: {primary_err}. "
                    f"Attempting cascade fallback to '{fb_model}'..."
                )
                try:
                    fb_config = self._build_gemini_config(
                        schema=config.response_schema if hasattr(config, "response_schema") else None
                    )

                    def _invoke_fallback():
                        fb_resp = self._gemini_client.models.generate_content(
                            model=fb_model,
                            contents=full_prompt,
                            config=fb_config,
                        )
                        if fb_resp and fb_resp.text:
                            return fb_resp.text
                        raise RuntimeError(f"Gemini returned empty response for fallback model {fb_model}")

                    return retry_sync(_invoke_fallback, max_retries=2, base_delay=2.0)
                except Exception as fb_err:
                    logger.error(f"Fallback to '{fb_model}' also failed: {fb_err}")

            raise primary_err

    async def _call_gemini_async(self, full_prompt: str, config=None) -> str:
        """Call Gemini asynchronously with automatic exponential backoff retry and model cascade."""
        if not self._gemini_client:
            raise RuntimeError("Gemini client is not initialized. Please configure GEMINI_API_KEY in .env.")

        async def _invoke_primary():
            resp = await self._gemini_client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=config,
            )
            if resp and resp.text:
                return resp.text
            raise RuntimeError(f"Gemini returned empty response for model {self.model}")

        try:
            return await retry_async(_invoke_primary, max_retries=3, base_delay=1.5)
        except Exception as primary_err:
            fallbacks = [m for m in GEMINI_FALLBACK_CANDIDATES if m != self.model]
            if not fallbacks and self.model == "gemini-3.5-flash-lite":
                fallbacks = ["gemini-3.5-flash"]
            elif not fallbacks and self.model == "gemini-3.5-flash":
                fallbacks = ["gemini-3.5-flash-lite"]

            for fb_model in fallbacks:
                logger.warning(
                    f"Primary Gemini model '{self.model}' failed after retries: {primary_err}. "
                    f"Attempting cascade async fallback to '{fb_model}'..."
                )
                try:
                    fb_config = self._build_gemini_config(
                        schema=config.response_schema if hasattr(config, "response_schema") else None
                    )

                    async def _invoke_fallback():
                        fb_resp = await self._gemini_client.aio.models.generate_content(
                            model=fb_model,
                            contents=full_prompt,
                            config=fb_config,
                        )
                        if fb_resp and fb_resp.text:
                            return fb_resp.text
                        raise RuntimeError(f"Gemini returned empty response for fallback model {fb_model}")

                    return await retry_async(_invoke_fallback, max_retries=2, base_delay=2.0)
                except Exception as fb_err:
                    logger.error(f"Async fallback to '{fb_model}' also failed: {fb_err}")

            raise primary_err

    # -------------------------------------------------------------
    # Structured Output APIs
    # -------------------------------------------------------------
    def extract_structured_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
    ) -> T:
        """Synchronous structured extraction into Pydantic model."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        if self.provider == "gemini":
            config = self._build_gemini_config(schema=schema)
            raw_text = self._call_gemini_sync(full_prompt=full_prompt, config=config)
            return schema.model_validate_json(raw_text)

        if self.provider == "openai" and self._openai_sync_client:
            response = self._openai_sync_client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=schema,
            )
            parsed = response.choices[0].message.parsed
            if parsed is not None:
                return parsed
            raise RuntimeError("OpenAI returned null structured output.")

        raise RuntimeError(f"No active LLM client configured for provider '{self.provider}'.")

    async def extract_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
    ) -> T:
        """Asynchronous structured extraction with retry."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        async def _call():
            if self.provider == "gemini":
                config = self._build_gemini_config(schema=schema)
                raw_text = await self._call_gemini_async(full_prompt=full_prompt, config=config)
                return schema.model_validate_json(raw_text)

            if self.provider == "openai" and self._openai_client:
                response = await self._openai_client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=schema,
                )
                parsed = response.choices[0].message.parsed
                if parsed is not None:
                    return parsed
                raise RuntimeError("OpenAI returned null structured output.")

            raise RuntimeError(f"No active LLM client configured for provider '{self.provider}'.")

        return await retry_async(_call, max_retries=3, base_delay=1.5)

    # -------------------------------------------------------------
    # Free-form Text Generation APIs
    # -------------------------------------------------------------
    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Synchronous long-form text generation (draft synthesis)."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        if self.provider == "gemini":
            config = self._build_gemini_config()
            return self._call_gemini_sync(full_prompt=full_prompt, config=config)

        if self.provider == "openai" and self._openai_sync_client:
            response = self._openai_sync_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            raise RuntimeError("OpenAI returned empty text content.")

        raise RuntimeError(f"No active LLM client configured for provider '{self.provider}'.")

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Asynchronous long-form text generation with retry."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        async def _call():
            if self.provider == "gemini":
                config = self._build_gemini_config()
                return await self._call_gemini_async(full_prompt=full_prompt, config=config)

            if self.provider == "openai" and self._openai_client:
                response = await self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                raise RuntimeError("OpenAI returned empty text content.")

            raise RuntimeError(f"No active LLM client configured for provider '{self.provider}'.")

        return await retry_async(_call, max_retries=3, base_delay=1.5)
