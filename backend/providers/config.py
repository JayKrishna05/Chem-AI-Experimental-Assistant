"""Provider configuration resolved from environment variables.

Environment variables
---------------------
ORD_PROVIDER
    Which provider to use.  Default: ``ollama``.
    Supported values: ``ollama``, ``openai``, ``anthropic``, ``gemini``, ``groq``.

ORD_PLANNER_MODEL
    Model to use for the planner role.  Default: ``qwen2.5:3b``.

ORD_ANALYSIS_MODEL
    Model to use for the analysis role.  Default: same as
    ``ORD_PLANNER_MODEL``.

ORD_OLLAMA_BASE_URL
    Base URL for the local Ollama server.  Default: ``http://localhost:11434``.

ORD_OPENAI_API_KEY
    OpenAI API key.  Required when ``ORD_PROVIDER=openai``.

ORD_ANTHROPIC_API_KEY
    Anthropic API key.  Required when ``ORD_PROVIDER=anthropic``.

ORD_GEMINI_API_KEY
    Google Gemini API key.  Required when ``ORD_PROVIDER=gemini``.

ORD_GROQ_API_KEY
    Groq API key.  Required when ``ORD_PROVIDER=groq``.
    Obtain from https://console.groq.com/keys
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


_DEFAULT_PROVIDER = "ollama"
_DEFAULT_PLANNER_MODEL = "qwen2.5:3b"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


@dataclass
class ProviderConfig:
    """Resolved provider configuration.

    All fields have defaults and can be overridden by environment
    variables.  Use :func:`load_config` to construct an instance from
    the current environment.
    """

    provider: str = _DEFAULT_PROVIDER
    """Active provider name.  One of ``ollama``, ``openai``, ``anthropic``,
    ``gemini``."""

    planner_model: str = _DEFAULT_PLANNER_MODEL
    """Model used for intent detection and tool selection."""

    analysis_model: str = field(init=False)
    """Model used for summarisation and comparison.  Defaults to
    ``planner_model`` if not explicitly set."""

    ollama_base_url: str = _DEFAULT_OLLAMA_BASE_URL
    """Base URL of the local Ollama server."""

    openai_api_key: str | None = None
    """OpenAI API key.  Required when ``provider == "openai"``."""

    anthropic_api_key: str | None = None
    """Anthropic API key.  Required when ``provider == "anthropic"``."""

    gemini_api_key: str | None = None
    """Google Gemini API key.  Required when ``provider == "gemini"``."""

    groq_api_key: str | None = None
    """Groq API key.  Required when ``provider == "groq"``."""

    _analysis_model_override: str | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        self.analysis_model = self._analysis_model_override or self.planner_model


def load_config() -> ProviderConfig:
    """Build a :class:`ProviderConfig` from the current environment.

    Reads ``ORD_*`` environment variables and falls back to safe defaults
    for any that are not set.

    Returns
    -------
    ProviderConfig
    """
    planner_model = os.environ.get("ORD_PLANNER_MODEL", _DEFAULT_PLANNER_MODEL)
    analysis_model_override = os.environ.get("ORD_ANALYSIS_MODEL")

    cfg = ProviderConfig(
        provider=os.environ.get("ORD_PROVIDER", _DEFAULT_PROVIDER).lower().strip(),
        planner_model=planner_model,
        ollama_base_url=os.environ.get(
            "ORD_OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL
        ).rstrip("/"),
        openai_api_key=os.environ.get("ORD_OPENAI_API_KEY"),
        anthropic_api_key=os.environ.get("ORD_ANTHROPIC_API_KEY"),
        gemini_api_key=os.environ.get("ORD_GEMINI_API_KEY"),
        groq_api_key=os.environ.get("ORD_GROQ_API_KEY"),
        _analysis_model_override=analysis_model_override,
    )
    return cfg
