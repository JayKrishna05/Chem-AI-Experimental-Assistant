"""Anthropic provider stub.

Status: NOT IMPLEMENTED — placeholder for Phase 5.

This module is intentionally incomplete.  Its purpose is to:

1. Reserve the correct module path so imports do not break.
2. Document exactly what needs to be implemented.
3. Raise a clear ``NotImplementedError`` so failures surface at call
   time, not at import time.

Implementation notes (for the developer who fills this in)
----------------------------------------------------------
- Install ``anthropic`` package: ``pip install anthropic>=0.25``
- Add ``ORD_ANTHROPIC_API_KEY`` to environment / ``.env`` file.
- Use ``anthropic.Anthropic(api_key=config.anthropic_api_key)`` to
  build the client.
- ``chat`` maps to ``client.messages.create(model=..., messages=[...])``;
  extract ``content[0].text`` from the response.
- ``generate`` can be implemented as a single ``user`` message.
- System messages must be passed via the separate ``system`` parameter
  in the Anthropic API, not as a message in the ``messages`` list.
- Add ``anthropic`` to ``requirements.txt`` when implementing.
"""

from __future__ import annotations

from typing import Any

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config


class AnthropicProvider(BaseProvider):
    """LLM provider backed by the Anthropic API (Claude models).

    .. warning::
        This provider is a stub and is **not yet implemented**.
        Calling ``chat`` or ``generate`` raises ``NotImplementedError``.

    Parameters
    ----------
    config:
        Optional :class:`~backend.providers.config.ProviderConfig`.
        Must contain a non-empty ``anthropic_api_key`` when implemented.
    default_model:
        Override the model used by this provider.
    """

    provider_name = "anthropic"

    def __init__(
        self,
        *,
        config: ProviderConfig | None = None,
        default_model: str = "claude-3-5-haiku-latest",
    ) -> None:
        self._config = config or load_config()
        self._default_model = default_model
        if not self._config.anthropic_api_key:
            raise ValueError(
                "Anthropic API key is not configured.  "
                "Set the ORD_ANTHROPIC_API_KEY environment variable."
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
            "AnthropicProvider.chat is not yet implemented.  "
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
            "AnthropicProvider.generate is not yet implemented.  "
            "See the module docstring for implementation guidance."
        )

    def list_models(self) -> list[str]:
        """Return known Anthropic model names (static list — no live API call yet)."""
        return [
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-3-5-haiku-latest",
            "claude-3-opus-latest",
        ]
