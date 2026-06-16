"""Ollama provider — live implementation using the Ollama REST API.

Ollama exposes two relevant endpoints:

POST /api/chat
    Multi-turn conversation.  Used by :meth:`OllamaProvider.chat`.

POST /api/generate
    Single-prompt completion.  Used by :meth:`OllamaProvider.generate`.

Both endpoints are called with ``stream=False`` so that responses are
returned as a single JSON object.  Streaming support can be added in a
future milestone when the ``POST /chat`` endpoint is built.

Configuration
-------------
Pass a :class:`~backend.providers.config.ProviderConfig` (or supply
``base_url`` and ``default_model`` directly) to override defaults.

Default base URL: ``http://localhost:11434``
Default model:    ``gemma4:12b-it-qat``
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config


_CHAT_PATH = "/api/chat"
_GENERATE_PATH = "/api/generate"
_TAGS_PATH = "/api/tags"
_CONNECT_TIMEOUT_S = 10


class OllamaConnectionError(RuntimeError):
    """Raised when the Ollama server cannot be reached."""


class OllamaResponseError(RuntimeError):
    """Raised when the Ollama server returns an unexpected response."""


class OllamaProvider(BaseProvider):
    """LLM provider backed by a locally running Ollama server.

    Parameters
    ----------
    base_url:
        Root URL of the Ollama HTTP server, without a trailing slash.
        Defaults to the value in ``config.ollama_base_url``.
    default_model:
        Model name to use when the caller does not supply one.
        Defaults to ``config.planner_model``.
    config:
        Optional :class:`~backend.providers.config.ProviderConfig`.
        If ``None``, :func:`~backend.providers.config.load_config` is
        called to build one from environment variables.
    timeout:
        HTTP timeout in seconds.  Default: 10.
    """

    provider_name = "ollama"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_model: str | None = None,
        config: ProviderConfig | None = None,
        timeout: float = _CONNECT_TIMEOUT_S,
    ) -> None:
        self._config = config or load_config()
        self._base_url = (base_url or self._config.ollama_base_url).rstrip("/")
        self._default_model = default_model or self._config.planner_model
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a multi-turn conversation to Ollama's ``/api/chat``.

        Parameters
        ----------
        messages:
            Ordered list of :class:`~backend.providers.base.Message`
            objects.
        model:
            Override the provider's default model.
        temperature:
            Sampling temperature passed to Ollama options.
        max_tokens:
            Maximum tokens to generate, passed as ``num_predict`` in
            Ollama options.

        Returns
        -------
        ChatResponse
        """
        resolved_model = model or self._default_model
        body: dict[str, Any] = {
            "model": resolved_model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
        }
        options = self._build_options(temperature=temperature, max_tokens=max_tokens)
        if options:
            body["options"] = options

        raw = self._post(_CHAT_PATH, body)
        content = raw.get("message", {}).get("content", "")
        return ChatResponse(
            content=content,
            model=raw.get("model", resolved_model),
            provider=self.provider_name,
            raw=raw,
        )

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> GenerateResponse:
        """Complete a single prompt via Ollama's ``/api/generate``.

        Parameters
        ----------
        prompt:
            Text prompt to complete.
        model:
            Override the provider's default model.
        temperature:
            Sampling temperature.
        max_tokens:
            Maximum tokens to generate (``num_predict``).

        Returns
        -------
        GenerateResponse
        """
        resolved_model = model or self._default_model
        body: dict[str, Any] = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
        }
        options = self._build_options(temperature=temperature, max_tokens=max_tokens)
        if options:
            body["options"] = options

        raw = self._post(_GENERATE_PATH, body)
        content = raw.get("response", "")
        return GenerateResponse(
            content=content,
            model=raw.get("model", resolved_model),
            provider=self.provider_name,
            raw=raw,
        )

    def list_models(self) -> list[str]:
        """Fetch available models from Ollama's /api/tags endpoint."""
        try:
            req = Request(self._base_url + _TAGS_PATH, method="GET")
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            # Fallback if offline or parsing fails
            return [self._default_model] if self._default_model else []

    # ------------------------------------------------------------------
    # Connectivity helper
    # ------------------------------------------------------------------

    def is_reachable(self) -> bool:
        """Return ``True`` if the Ollama server responds to a HEAD request.

        Used by tests to conditionally skip live integration tests.
        """
        try:
            req = Request(self._base_url, method="HEAD")
            with urlopen(req, timeout=self._timeout):
                pass
            return True
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_options(
        *,
        temperature: float | None,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = float(temperature)
        if max_tokens is not None:
            options["num_predict"] = int(max_tokens)
        return options

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = self._base_url + path
        payload = json.dumps(body).encode("utf-8")
        req = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self._timeout) as resp:
                raw_bytes = resp.read()
        except URLError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {self._base_url}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise OllamaConnectionError(
                f"Network error connecting to Ollama at {self._base_url}: {exc}"
            ) from exc

        try:
            return json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError(
                f"Ollama returned non-JSON response: {raw_bytes[:200]!r}"
            ) from exc
