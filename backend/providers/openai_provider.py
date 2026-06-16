"""OpenAI provider stub.

Status: NOT IMPLEMENTED — placeholder for Phase 5.

This module is intentionally incomplete.  Its purpose is to:

1. Reserve the correct module path so imports do not break.
2. Document exactly what needs to be implemented.
3. Raise a clear ``NotImplementedError`` so failures surface at call
   time, not at import time.

Implementation notes (for the developer who fills this in)
----------------------------------------------------------
- Install ``openai`` package: ``pip install openai>=1.0``
- Add ``ORD_OPENAI_API_KEY`` to environment / ``.env`` file.
- Use ``openai.OpenAI(api_key=config.openai_api_key)`` to build the
  client.
- ``chat`` maps to ``client.chat.completions.create(model=...,
  messages=[...])``; extract ``choices[0].message.content``.
- ``generate`` can be implemented as a single ``user`` message sent to
  ``chat.completions.create``.
- ``ChatResponse`` and ``GenerateResponse`` should mirror the structure
  already defined in ``base.py``.
- Add ``openai`` to ``requirements.txt`` when implementing.
"""

from __future__ import annotations

from typing import Any

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config


class OpenAIProvider(BaseProvider):
    """LLM provider backed by the OpenAI API.

    .. warning::
        This provider is a stub and is **not yet implemented**.
        Calling ``chat`` or ``generate`` raises ``NotImplementedError``.

    Parameters
    ----------
    config:
        Optional :class:`~backend.providers.config.ProviderConfig`.
        Must contain a non-empty ``openai_api_key`` when implemented.
    default_model:
        Override the model used by this provider.
    """

    provider_name = "openai"

    def __init__(
        self,
        *,
        config: ProviderConfig | None = None,
        default_model: str = "gpt-4o-mini",
    ) -> None:
        self._config = config or load_config()
        self._default_model = default_model
        # Validate that a key is configured so misconfiguration surfaces early.
        if not self._config.openai_api_key:
            raise ValueError(
                "OpenAI API key is not configured.  "
                "Set the ORD_OPENAI_API_KEY environment variable."
            )

    def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        raise NotImplementedError(
            "OpenAIProvider.chat is not yet implemented.  "
            "See the module docstring for implementation guidance."
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
        raise NotImplementedError(
            "OpenAIProvider.generate is not yet implemented.  "
            "See the module docstring for implementation guidance."
        )
