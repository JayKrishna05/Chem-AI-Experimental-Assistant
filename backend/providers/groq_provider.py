"""Groq provider — live implementation using the Groq REST API.

Groq exposes an OpenAI-compatible chat completions endpoint:

POST https://api.groq.com/openai/v1/chat/completions
    Multi-turn conversation.  Used by :meth:`GroqProvider.chat` and
    :meth:`GroqProvider.generate`.

GET  https://api.groq.com/openai/v1/models
    Model discovery.  Used by :meth:`GroqProvider.list_models`.

Both endpoints use the standard OpenAI message format so conversion is
straightforward.

Configuration
-------------
Set ``ORD_GROQ_API_KEY`` in the environment (or a ``.env`` file) before
using this provider.

Default model: ``llama-3.3-70b-versatile``

Example
-------
::

    import os
    os.environ["ORD_GROQ_API_KEY"] = "gsk_..."

    from backend.providers import get_provider
    provider = get_provider("groq")
    resp = provider.chat([Message(role="user", content="Hello")])
    print(resp.content)
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config


_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_CHAT_PATH = "/chat/completions"
_MODELS_PATH = "/models"

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_CONNECT_TIMEOUT_S = 10.0

# Models that are available on Groq (fallback if the live /models call fails)
_FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "gemma-7b-it",
    "mixtral-8x7b-32768",
    "qwen-qwq-32b",
    "deepseek-r1-distill-llama-70b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]


class GroqConnectionError(RuntimeError):
    """Raised when the Groq API cannot be reached."""


class GroqAPIError(RuntimeError):
    """Raised when the Groq API returns an error response."""


class GroqProvider(BaseProvider):
    """LLM provider backed by the Groq cloud API.

    Groq uses an OpenAI-compatible REST API, so the implementation mirrors
    standard chat completions semantics.

    Parameters
    ----------
    default_model:
        Model name to use when the caller does not supply one.
        Default: ``llama-3.3-70b-versatile``.
    config:
        Optional :class:`~backend.providers.config.ProviderConfig`.
        If ``None``, :func:`~backend.providers.config.load_config` is called.
    timeout:
        HTTP timeout in seconds.  Default: 10.
    """

    provider_name = "groq"

    def __init__(
        self,
        *,
        default_model: str = _DEFAULT_MODEL,
        config: ProviderConfig | None = None,
        timeout: float = _CONNECT_TIMEOUT_S,
    ) -> None:
        self._config = config or load_config()
        if not self._config.groq_api_key:
            raise ValueError(
                "Groq API key is not configured.  "
                "Set the ORD_GROQ_API_KEY environment variable.  "
                "Get a key at https://console.groq.com/keys"
            )
        self._api_key = self._config.groq_api_key
        self._default_model = default_model
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        timeout: float | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a multi-turn conversation to Groq's chat completions endpoint.

        Parameters
        ----------
        messages:
            Ordered list of :class:`~backend.providers.base.Message` objects.
        model:
            Override the provider's default model.
        timeout:
            Per-call timeout in seconds.  Falls back to provider default.
        temperature:
            Sampling temperature (0.0 – 2.0).
        max_tokens:
            Maximum tokens to generate.

        Returns
        -------
        ChatResponse
        """
        resolved_model = model or self._default_model
        body: dict[str, Any] = {
            "model": resolved_model,
            "messages": [m.to_dict() for m in messages],
        }
        if temperature is not None:
            body["temperature"] = float(temperature)
        if max_tokens is not None:
            body["max_tokens"] = int(max_tokens)

        raw = self._post(_CHAT_PATH, body, timeout=timeout)
        choices = raw.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        actual_model = raw.get("model", resolved_model)

        return ChatResponse(
            content=content,
            model=actual_model,
            provider=self.provider_name,
            raw=raw,
        )

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> GenerateResponse:
        """Complete a single prompt via Groq's chat completions endpoint.

        Internally wraps the prompt as a single ``user`` message.

        Parameters
        ----------
        prompt:
            Text to complete.
        model:
            Override the provider's default model.
        timeout:
            Per-call timeout in seconds.
        temperature:
            Sampling temperature.
        max_tokens:
            Maximum tokens to generate.

        Returns
        -------
        GenerateResponse
        """
        messages = [Message(role="user", content=prompt)]
        chat_resp = self.chat(
            messages,
            model=model,
            timeout=timeout,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return GenerateResponse(
            content=chat_resp.content,
            model=chat_resp.model,
            provider=self.provider_name,
            raw=chat_resp.raw,
        )

    def list_models(self) -> list[str]:
        """Fetch available model IDs from Groq's /models endpoint.

        Returns the live list when reachable; falls back to a static list
        on network errors to keep the UI functional even without a key.
        """
        try:
            req = Request(
                _GROQ_BASE_URL + _MODELS_PATH,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                method="GET",
            )
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
            # Filter to chat models only (exclude whisper/tts)
            models = [
                m["id"]
                for m in data.get("data", [])
                if not any(skip in m["id"].lower() for skip in ("whisper", "tts"))
            ]
            return sorted(models) if models else _FALLBACK_MODELS
        except Exception:
            return list(_FALLBACK_MODELS)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, body: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        """POST a JSON payload to the Groq API and return the parsed response."""
        url = _GROQ_BASE_URL + path
        payload = json.dumps(body).encode("utf-8")
        req = Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            method="POST",
        )
        effective_timeout = timeout or self._timeout
        print(f"[GroqProvider] POST {path} model={body.get('model')} timeout={effective_timeout}s")
        try:
            with urlopen(req, timeout=effective_timeout) as resp:
                raw_bytes = resp.read()
        except HTTPError as exc:
            raw_bytes = exc.read()
        except URLError as exc:
            raise GroqConnectionError(
                f"Cannot reach Groq API at {url}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise GroqConnectionError(
                f"Network error connecting to Groq API: {exc}"
            ) from exc

        try:
            parsed = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise GroqAPIError(
                f"Groq returned non-JSON response: {raw_bytes[:200]!r}"
            ) from exc

        # Surface API-level errors
        if "error" in parsed:
            err = parsed["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise GroqAPIError(f"Groq API error: {msg}")

        return parsed
