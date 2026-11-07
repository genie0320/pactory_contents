"""Langfuse Observability & Tracing Integration.

Follows Langfuse AI skill best practices:
- Graceful degradation when credentials are not configured (zero runtime overhead).
- Automatic hierarchical span and generation tracking using context managers.
- Model, token usage, cost, and latency metrics collection.
- Verb-first descriptive naming convention (e.g. 'plan-blueprint', 'synthesize-draft').
- Multi-step parent-child nesting for pipelines.
- Clean flushing on script exit and FastAPI lifecycle shutdown.
"""

from __future__ import annotations

import atexit
import contextlib
import logging
import os
from typing import Any

logger = logging.getLogger("pactory.observability")

_langfuse_client: Any | None = None
_client_initialized = False


def get_langfuse() -> Any | None:
    """Lazily initialize and return the global Langfuse client instance."""
    global _langfuse_client, _client_initialized
    if _client_initialized:
        return _langfuse_client

    pub_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    sec_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"

    if pub_key and sec_key:
        try:
            from langfuse import Langfuse

            _langfuse_client = Langfuse(
                public_key=pub_key,
                secret_key=sec_key,
                host=host,
            )
            logger.info("Langfuse client successfully initialized (%s)", host)
        except Exception as exc:
            logger.debug("Failed to initialize Langfuse client: %s", exc)
            _langfuse_client = None
    else:
        _langfuse_client = None

    _client_initialized = True
    return _langfuse_client


def flush_langfuse() -> None:
    """Flush any pending events to Langfuse."""
    lf = get_langfuse()
    if lf is not None:
        try:
            lf.flush()
        except Exception as exc:
            logger.debug("Langfuse flush failed: %s", exc)


def shutdown_langfuse() -> None:
    """Flush and shut down Langfuse background worker threads."""
    lf = get_langfuse()
    if lf is not None:
        try:
            lf.shutdown()
        except Exception as exc:
            logger.debug("Langfuse shutdown failed: %s", exc)


# Flush on interpreter exit
try:
    atexit.register(flush_langfuse)
except Exception:
    pass


@contextlib.contextmanager
def trace_observation(
    name: str,
    as_type: str = "span",
    input_data: Any = None,
    output_data: Any = None,
    metadata: dict[str, Any] | None = None,
    model: str | None = None,
    usage_details: dict[str, int] | None = None,
    cost_details: dict[str, float] | None = None,
):
    """Context manager for tracing operations following Langfuse best practices.

    If Langfuse is not enabled, seamlessly acts as a no-op nullcontext.
    When active, creates an observation that automatically nests under the current active span.
    """
    lf = get_langfuse()
    if lf is None:
        yield None
        return

    kwargs: dict[str, Any] = {
        "name": name,
        "as_type": as_type,
        "input": input_data,
        "metadata": metadata or {},
    }
    if output_data is not None:
        kwargs["output"] = output_data
    if model is not None:
        kwargs["model"] = model
    if usage_details is not None:
        kwargs["usage_details"] = usage_details
    if cost_details is not None:
        kwargs["cost_details"] = cost_details

    cm = None
    obs = None
    try:
        cm = lf.start_as_current_observation(**kwargs)
        obs = cm.__enter__()
    except Exception as exc:
        logger.debug("Failed to start Langfuse observation [%s]: %s", name, exc)
        yield None
        return

    try:
        yield obs
    except Exception as exc:
        if obs is not None:
            try:
                obs.update(level="ERROR", status_message=str(exc))
            except Exception:
                pass
        if cm is not None:
            cm.__exit__(type(exc), exc, exc.__traceback__)
        raise
    else:
        if cm is not None:
            cm.__exit__(None, None, None)
