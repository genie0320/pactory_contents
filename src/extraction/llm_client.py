"""Multi-LLM Provider abstraction and universal LLM client.

Supports Google Gemini, Anthropic Claude, OpenAI, and Local Ollama models
with unified structured extraction, free-form text synthesis, dense embeddings,
and latency/token observability tracking.
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from src.exceptions import LLMServiceError
from src.observability import trace_observation

logger = logging.getLogger("llm_client")
T = TypeVar("T", bound=BaseModel)

GEMINI_FALLBACK_CANDIDATES = ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-3.5-flash"]


def _run_sync(coro: Any) -> Any:
    """Run an async coroutine synchronously, safely handling running event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


# -------------------------------------------------------------
# 1. Base Provider Interface (Async-first with inherited sync wrappers)
# -------------------------------------------------------------
class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        pass

    def generate_text_sync(self, system_prompt: str, user_prompt: str, model: str) -> str:
        return _run_sync(self.generate_text(system_prompt, user_prompt, model))

    @abstractmethod
    async def extract_structured(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        pass

    def extract_structured_sync(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        return _run_sync(self.extract_structured(system_prompt, user_prompt, schema, model))

    @abstractmethod
    async def get_embedding(self, text: str, model: str) -> list[float]:
        pass

    def get_embedding_sync(self, text: str, model: str = "") -> list[float]:
        return _run_sync(self.get_embedding(text, model))


# -------------------------------------------------------------
# 2. Google Gemini Provider
# -------------------------------------------------------------
class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider via official google-genai SDK."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._client = None
        if self.api_key:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)

    def _build_config(self, schema=None):
        from google.genai import types
        if schema:
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.3,
            )
        return types.GenerateContentConfig(temperature=0.7)

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        if not self._client:
            raise LLMServiceError("GEMINI_API_KEY is not configured.")
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        config = self._build_config()

        target_model = model
        last_err = None
        for attempt in range(3):
            try:
                coro = self._client.aio.models.generate_content(
                    model=target_model,
                    contents=full_prompt,
                    config=config,
                )
                resp = await asyncio.wait_for(coro, timeout=45.0)
                if resp and resp.text:
                    return resp.text
                raise RuntimeError("Gemini returned empty text response.")
            except Exception as e:
                last_err = e
                logger.warning(f"Gemini text generation attempt #{attempt + 1} ({target_model}) failed: {e}")
                if attempt == 2:
                    break
                await asyncio.sleep(2.0 * (attempt + 1))
        raise last_err or RuntimeError("Gemini text generation failed after retries")

    async def extract_structured(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        if not self._client:
            raise LLMServiceError("GEMINI_API_KEY is not configured.")
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        config = self._build_config(schema=schema)

        target_model = model
        last_err = None
        for attempt in range(3):
            try:
                coro = self._client.aio.models.generate_content(
                    model=target_model,
                    contents=full_prompt,
                    config=config,
                )
                resp = await asyncio.wait_for(coro, timeout=35.0)
                if resp and resp.text:
                    return schema.model_validate_json(resp.text)
                raise RuntimeError("Gemini returned empty structured output.")
            except Exception as e:
                last_err = e
                logger.warning(f"Gemini structured extraction attempt #{attempt + 1} ({target_model}) failed: {e}")
                if attempt == 2:
                    break
                await asyncio.sleep(2.0 * (attempt + 1))
        raise last_err or RuntimeError("Gemini structured extraction failed after retries")

    async def get_embedding(self, text: str, model: str = "gemini-embedding-001") -> list[float]:
        if not self._client:
            return _pseudo_embedding(text)
        try:
            resp = await self._client.aio.models.embed_content(
                model=model,
                contents=text,
            )
            if resp and hasattr(resp, "embedding") and resp.embedding:
                return resp.embedding.values
            if resp and hasattr(resp, "embeddings") and resp.embeddings:
                return resp.embeddings[0].values
        except Exception as e:
            logger.warning(f"Gemini embedding API call failed ({e}), falling back to pseudo-dense vector.")
        return _pseudo_embedding(text)


# -------------------------------------------------------------
# 3. OpenAI Provider
# -------------------------------------------------------------
class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider via openai SDK."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = None
        if self.api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        if not self._client:
            raise LLMServiceError("OPENAI_API_KEY is not configured.")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        resp = await self._client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content or ""

    async def extract_structured(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        if not self._client:
            raise LLMServiceError("OPENAI_API_KEY is not configured.")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        resp = await self._client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=schema,
        )
        parsed = resp.choices[0].message.parsed
        if parsed is not None:
            return parsed
        raise RuntimeError("OpenAI returned null structured output.")

    async def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        if not self._client:
            return _pseudo_embedding(text)
        try:
            resp = await self._client.embeddings.create(model=model, input=text)
            return resp.data[0].embedding
        except Exception:
            return _pseudo_embedding(text)


# -------------------------------------------------------------
# 4. Anthropic Claude Provider
# -------------------------------------------------------------
class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider via anthropic SDK."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._client = None
        if self.api_key:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        if not self._client:
            raise LLMServiceError("ANTHROPIC_API_KEY is not configured.")
        resp = await self._client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt or "",
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text if resp.content else ""

    async def extract_structured(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        augmented_system = (
            f"{system_prompt}\n\nIMPORTANT: Respond strictly with a JSON object conforming to this schema:\n{schema_json}\n"
            "Do NOT wrap with markdown code blocks. Return raw JSON only."
        )
        raw_text = await self.generate_text(augmented_system, user_prompt, model)
        return _clean_and_parse_json(raw_text, schema)

    async def get_embedding(self, text: str, model: str = "") -> list[float]:
        return _pseudo_embedding(text)


# -------------------------------------------------------------
# 5. Local Ollama Provider (DeepSeek-R1 / Llama 3)
# -------------------------------------------------------------
class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider for free, on-premise execution (DeepSeek-R1 / Llama 3)."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(url, json={"model": model, "messages": messages, "stream": False})
                res.raise_for_status()
                data = res.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            raise LLMServiceError(f"Ollama connection error at {self.base_url}: {e}")

    async def extract_structured(self, system_prompt: str, user_prompt: str, schema: type[T], model: str) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        augmented_system = (
            f"{system_prompt}\n\nIMPORTANT: Output valid JSON only matching schema:\n{schema_json}"
        )
        raw_text = await self.generate_text(augmented_system, user_prompt, model)
        return _clean_and_parse_json(raw_text, schema)

    async def get_embedding(self, text: str, model: str = "nomic-embed-text") -> list[float]:
        url = f"{self.base_url}/api/embeddings"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json={"model": model, "prompt": text})
                if res.status_code == 200:
                    return res.json().get("embedding", [])
        except Exception:
            pass
        return _pseudo_embedding(text)


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------
def _clean_and_parse_json(raw_text: str, schema: type[T]) -> T:
    """Clean markdown triple backticks and parse into Pydantic schema."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    return schema.model_validate_json(cleaned)


def _pseudo_embedding(text: str, dims: int = 128) -> list[float]:
    """Deterministic hash-based dense embedding fallback for offline/test environments."""
    import hashlib
    import math

    vector = [0.0] * dims
    tokens = text.lower().split()
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(dims):
            val = ((h >> (i % 64)) & 0xFF) / 255.0 - 0.5
            vector[i] += val

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


# -------------------------------------------------------------
# 6. Universal LLMClient Wrapper with Observability
# -------------------------------------------------------------
class LLMClient:
    """Universal LLM client orchestrating providers and tracking usage/latency."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        repo: Any | None = None,
    ):
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            try:
                from src.config import load_env_file
                load_env_file()
            except Exception:
                pass

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        claude_key = os.getenv("ANTHROPIC_API_KEY")

        chosen_provider = (
            provider
            or os.getenv("DEFAULT_LLM_PROVIDER", "").lower()
            or os.getenv("LLM_PROVIDER", "").lower()
        )
        if not chosen_provider:
            if gemini_key:
                chosen_provider = "gemini"
            elif claude_key:
                chosen_provider = "claude"
            elif openai_key:
                chosen_provider = "openai"
            else:
                chosen_provider = "gemini"

        self.provider = chosen_provider
        self.repo = repo

        if self.provider == "gemini":
            self.model = model or os.getenv("DEFAULT_MODEL", "gemini-3-flash-preview")
            self.api_key = api_key or gemini_key
            self._adapter = GeminiProvider(api_key=self.api_key)
        elif self.provider == "claude":
            self.model = model or os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest")
            self.api_key = api_key or claude_key
            self._adapter = ClaudeProvider(api_key=self.api_key)
        elif self.provider == "openai":
            self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
            self.api_key = api_key or openai_key
            self._adapter = OpenAIProvider(api_key=self.api_key)
        elif self.provider == "ollama":
            self.model = model or os.getenv("DEFAULT_MODEL", "deepseek-r1:latest")
            self.api_key = "local-ollama"
            self._adapter = OllamaProvider()
        else:
            self.model = model or os.getenv("DEFAULT_MODEL", "gemini-3-flash-preview")
            self.api_key = api_key or gemini_key
            self._adapter = GeminiProvider(api_key=self.api_key)

    def _calculate_usage(self, prompt_text: str, completion_text: str) -> tuple[int, int, float]:
        """Estimate token counts and cost for the active model."""
        prompt_tokens = max(1, len(prompt_text) // 3)
        completion_tokens = max(1, len(completion_text) // 3)

        pricing = {
            "gemini-3-flash-preview": (0.15, 0.60),
            "gemini-3.5-flash-lite": (0.075, 0.30),
            "gemini-3.5-flash": (0.15, 0.60),
            "gemini-3.8-flash": (0.15, 0.60),
            "gemini-3.8-pro": (1.25, 5.00),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (2.50, 10.00),
            "claude-3-7-sonnet-latest": (3.00, 15.00),
            "claude-3-5-haiku-latest": (0.80, 4.00),
            "deepseek-r1:latest": (0.0, 0.0),
        }
        in_price, out_price = pricing.get(self.model, (0.15, 0.60))
        cost = (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000.0
        return prompt_tokens, completion_tokens, cost

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: str = "generate_text",
    ) -> str:
        """Asynchronous text generation."""
        t0 = time.perf_counter()
        input_payload = {"system": system_prompt, "prompt": user_prompt}
        with trace_observation(
            name=f"pactory:{task_type}",
            as_type="generation",
            model=self.model,
            input_data=input_payload,
            metadata={"provider": self.provider, "task_type": task_type},
        ) as obs:
            res = await self._adapter.generate_text(system_prompt, user_prompt, self.model)
            latency = (time.perf_counter() - t0) * 1000.0
            p_tok, c_tok, cost = self._calculate_usage(f"{system_prompt} {user_prompt}", res)
            if obs is not None:
                try:
                    obs.update(
                        output=res,
                        usage_details={"input": p_tok, "output": c_tok, "total": p_tok + c_tok},
                        cost_details={"total": cost},
                        metadata={"provider": self.provider, "latency_ms": latency},
                    )
                except Exception:
                    pass
            if self.repo:
                try:
                    self.repo.log_llm_usage(
                        task_type=task_type,
                        provider=self.provider,
                        model=self.model,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        latency_ms=latency,
                        estimated_cost_usd=cost,
                    )
                except Exception:
                    pass
            return res

    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: str = "generate_text_sync",
    ) -> str:
        """Synchronous text generation."""
        t0 = time.perf_counter()
        input_payload = {"system": system_prompt, "prompt": user_prompt}
        with trace_observation(
            name=f"pactory:{task_type}",
            as_type="generation",
            model=self.model,
            input_data=input_payload,
            metadata={"provider": self.provider, "task_type": task_type},
        ) as obs:
            res = self._adapter.generate_text_sync(system_prompt, user_prompt, self.model)
            latency = (time.perf_counter() - t0) * 1000.0
            p_tok, c_tok, cost = self._calculate_usage(f"{system_prompt} {user_prompt}", res)
            if obs is not None:
                try:
                    obs.update(
                        output=res,
                        usage_details={"input": p_tok, "output": c_tok, "total": p_tok + c_tok},
                        cost_details={"total": cost},
                        metadata={"provider": self.provider, "latency_ms": latency},
                    )
                except Exception:
                    pass
            if self.repo:
                try:
                    self.repo.log_llm_usage(
                        task_type=task_type,
                        provider=self.provider,
                        model=self.model,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        latency_ms=latency,
                        estimated_cost_usd=cost,
                    )
                except Exception:
                    pass
            return res

    async def extract_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        task_type: str = "extract_structured",
    ) -> T:
        """Asynchronous structured extraction."""
        t0 = time.perf_counter()
        input_payload = {"system": system_prompt, "prompt": user_prompt, "schema": schema.__name__}
        with trace_observation(
            name=f"pactory:{task_type}",
            as_type="generation",
            model=self.model,
            input_data=input_payload,
            metadata={"provider": self.provider, "task_type": task_type, "schema": schema.__name__},
        ) as obs:
            res = await self._adapter.extract_structured(system_prompt, user_prompt, schema, self.model)
            latency = (time.perf_counter() - t0) * 1000.0
            output_dump = res.model_dump() if hasattr(res, "model_dump") else str(res)
            p_tok, c_tok, cost = self._calculate_usage(f"{system_prompt} {user_prompt}", str(output_dump))
            if obs is not None:
                try:
                    obs.update(
                        output=output_dump,
                        usage_details={"input": p_tok, "output": c_tok, "total": p_tok + c_tok},
                        cost_details={"total": cost},
                        metadata={"provider": self.provider, "latency_ms": latency},
                    )
                except Exception:
                    pass
            if self.repo:
                try:
                    self.repo.log_llm_usage(
                        task_type=task_type,
                        provider=self.provider,
                        model=self.model,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        latency_ms=latency,
                        estimated_cost_usd=cost,
                    )
                except Exception:
                    pass
            return res

    def extract_structured_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        task_type: str = "extract_structured_sync",
    ) -> T:
        """Synchronous structured extraction."""
        t0 = time.perf_counter()
        input_payload = {"system": system_prompt, "prompt": user_prompt, "schema": schema.__name__}
        with trace_observation(
            name=f"pactory:{task_type}",
            as_type="generation",
            model=self.model,
            input_data=input_payload,
            metadata={"provider": self.provider, "task_type": task_type, "schema": schema.__name__},
        ) as obs:
            res = self._adapter.extract_structured_sync(system_prompt, user_prompt, schema, self.model)
            latency = (time.perf_counter() - t0) * 1000.0
            output_dump = res.model_dump() if hasattr(res, "model_dump") else str(res)
            p_tok, c_tok, cost = self._calculate_usage(f"{system_prompt} {user_prompt}", str(output_dump))
            if obs is not None:
                try:
                    obs.update(
                        output=output_dump,
                        usage_details={"input": p_tok, "output": c_tok, "total": p_tok + c_tok},
                        cost_details={"total": cost},
                        metadata={"provider": self.provider, "latency_ms": latency},
                    )
                except Exception:
                    pass
            if self.repo:
                try:
                    self.repo.log_llm_usage(
                        task_type=task_type,
                        provider=self.provider,
                        model=self.model,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        latency_ms=latency,
                        estimated_cost_usd=cost,
                    )
                except Exception:
                    pass
            return res

    async def get_embedding(self, text: str, model: str | None = None) -> list[float]:
        """Generate dense embedding vector."""
        if model:
            return await self._adapter.get_embedding(text, model)
        return await self._adapter.get_embedding(text)

    def get_embedding_sync(self, text: str, model: str | None = None) -> list[float]:
        """Synchronously generate dense embedding vector."""
        if model:
            return self._adapter.get_embedding_sync(text, model)
        return self._adapter.get_embedding_sync(text)
