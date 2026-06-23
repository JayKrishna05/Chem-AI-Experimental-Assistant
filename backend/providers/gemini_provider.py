"""Gemini provider stub.

Status: NOT IMPLEMENTED — placeholder for Phase 5.

This module is intentionally incomplete.  Its purpose is to:

1. Reserve the correct module path so imports do not break.
2. Document exactly what needs to be implemented.
3. Raise a clear ``NotImplementedError`` so failures surface at call
   time, not at import time.

Implementation notes (for the developer who fills this in)
----------------------------------------------------------
- Install ``google-genai`` package: ``pip install google-genai>=1.0``
- Add ``ORD_GEMINI_API_KEY`` to environment / ``.env`` file.
- Use ``from google import genai; client = genai.Client(api_key=...)``
  to build the client.
- ``chat`` maps to ``client.models.generate_content(model=...,
  contents=[...])``.  The Gemini SDK uses a different message format;
  convert ``Message`` objects into ``google.genai.types.Content``
  objects.
- Role mapping: ``"assistant"`` → ``"model"`` in the Gemini SDK.
- Add ``google-genai`` to ``requirements.txt`` when implementing.
"""

from __future__ import annotations

from typing import Any

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config


class GeminiProvider(BaseProvider):
    """LLM provider backed by the Google Gemini API.

    .. warning::
        This provider is a stub and is **not yet implemented**.
        Calling ``chat`` or ``generate`` raises ``NotImplementedError``.

    Parameters
    ----------
    config:
        Optional :class:`~backend.providers.config.ProviderConfig`.
        Must contain a non-empty ``gemini_api_key`` when implemented.
    default_model:
        Override the model used by this provider.
    """

    provider_name = "gemini"

    def __init__(
        self,
        *,
        config: ProviderConfig | None = None,
        default_model: str = "gemini-2.0-flash",
    ) -> None:
        self._config = config or load_config()
        self._default_model = default_model
        if not self._config.gemini_api_key:
            raise ValueError(
                "Gemini API key is not configured.  "
                "Set the ORD_GEMINI_API_KEY environment variable."
            )

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
        raise NotImplementedError(
            "GeminiProvider.chat is not yet implemented.  "
            "See the module docstring for implementation guidance."
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
        raise NotImplementedError(
            "GeminiProvider.generate is not yet implemented.  "
            "See the module docstring for implementation guidance."
        )

    def list_models(self) -> list[str]:
        """Return known Gemini model names (static list — no live API call yet)."""
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
        ]
