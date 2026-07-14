import contextvars
import os
from typing import Callable, Optional, Type, TypeVar

from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

load_dotenv()

TModel = TypeVar("TModel", bound=BaseModel)

_MODEL_NAME = "gemini-2.0-flash-lite"


# ── API Key Pool ──────────────────────────────────────────────────────────────
# To add keys: set GEMINI_API_KEYS as a comma-separated list in your .env / env vars.
# Example: GEMINI_API_KEYS=key1,key2,key3,key4,key5
# Falls back to GEMINI_API_KEY (single key) for backwards compatibility.
def _load_keys() -> list[str]:
    keys_str = os.environ.get("GEMINI_API_KEYS", "").strip()
    if keys_str:
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if keys:
            return keys
    # Legacy single-key fallback
    single = os.environ.get("GEMINI_API_KEY", "").strip()
    return [single] if single else []


_KEY_LIST: list[str] = _load_keys()


# ── Progress Callback (thread + async safe via contextvars) ──────────────────
# contextvars.ContextVar is propagated automatically to ThreadPoolExecutor workers
# (used by LangGraph for parallel nodes) and asyncio tasks.
_progress_cb_var: contextvars.ContextVar[Optional[Callable[[str], None]]] = (
    contextvars.ContextVar("_gemini_progress_cb", default=None)
)


def set_progress_callback(fn: Callable[[str], None]) -> None:
    """Register a callback that receives progress messages for the current request."""
    _progress_cb_var.set(fn)


def clear_progress_callback() -> None:
    _progress_cb_var.set(None)


def emit_progress(message: str) -> None:
    """
    Emit a progress message to whoever is listening (SSE stream).
    Safe to call from any thread — no-op when no callback is registered.
    """
    fn = _progress_cb_var.get()
    if fn is not None:
        try:
            fn(message)
        except Exception:
            pass  # Never crash the pipeline because of a progress emit failure


# ── Key-Rotating LLM Chain ───────────────────────────────────────────────────

class _KeyRotatingChain:
    """
    Wraps a LangChain structured-output chain with transparent API key rotation.
    On ResourceExhausted (rate limit / quota exceeded) for one key, rotates to
    the next key in _KEY_LIST and retries. Only fails when ALL keys are exhausted
    for the same call.

    Adding more keys: just add them to GEMINI_API_KEYS env var (comma-separated).
    No code changes needed.
    """

    def __init__(self, schema: Type[TModel], temperature: float, timeout_s: float):
        self._schema = schema
        self._temperature = temperature
        self._timeout_s = timeout_s

    def invoke(self, messages):
        if not _KEY_LIST:
            raise RuntimeError(
                "No Gemini API keys configured. "
                "Set GEMINI_API_KEYS=key1,key2,... or GEMINI_API_KEY=key in your environment."
            )

        last_exc: Optional[Exception] = None

        for i, key in enumerate(_KEY_LIST):
            try:
                llm = ChatGoogleGenerativeAI(
                    model=_MODEL_NAME,
                    temperature=self._temperature,
                    google_api_key=key,
                    timeout=self._timeout_s,
                )
                chain = llm.with_structured_output(self._schema)
                return chain.invoke(messages)

            except Exception as e:
                err_msg = str(e)
                # Detect 429 quota exhaustion (including LangChain's wrapped ChatGoogleGenerativeAIError)
                is_quota_error = (
                    isinstance(e, ResourceExhausted) or 
                    "429" in err_msg or 
                    "RESOURCE_EXHAUSTED" in err_msg or 
                    "quota" in err_msg.lower()
                )
                
                if is_quota_error:
                    last_exc = e
                    if i < len(_KEY_LIST) - 1:
                        emit_progress("API key limit reached, trying a different one...")
                    else:
                        emit_progress("All API keys exhausted.")
                else:
                    # Non-quota errors (invalid key auth, parsing, network downtime) propagate immediately
                    raise

        raise last_exc or RuntimeError("All API keys failed.")


def get_structured_llm(
    schema: Type[TModel],
    temperature: float = 0.7,
    timeout_s: float = 240,
) -> _KeyRotatingChain:
    """
    Returns a chain that outputs a validated instance of `schema`.
    Automatically rotates through all configured Gemini API keys on rate limits.
    Drop-in replacement for the previous single-key implementation.
    """
    return _KeyRotatingChain(schema, temperature, timeout_s)
