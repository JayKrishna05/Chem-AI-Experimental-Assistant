"""Provider factory — the single place that resolves a provider name to an instance.

Business logic (the planner, future chat endpoints) should only call
:func:`get_provider`.  They must never instantiate a concrete provider
class directly.

Supported providers
-------------------
``ollama``
    Local Ollama server.  Default.
``openai``
    OpenAI API (stub — not yet implemented).
``anthropic``
    Anthropic API (stub — not yet implemented).
``gemini``
    Google Gemini API (stub — not yet implemented).

Configuration
-------------
Provider selection is driven by :func:`~backend.providers.config.load_config`,
which reads ``ORD_PROVIDER`` from the environment.  This can be
overridden by passing an explicit ``provider_name`` argument to
:func:`get_provider`.
"""

from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import BaseProvider
from .config import ProviderConfig, load_config
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider


# Registry maps provider name → constructor.
# Adding a new provider only requires adding an entry here.
_PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}

SUPPORTED_PROVIDERS: frozenset[str] = frozenset(_PROVIDER_REGISTRY)
"""Names of all providers known to the factory."""


class UnknownProviderError(ValueError):
    """Raised when an unrecognised provider name is requested."""


def get_provider(
    provider_name: str | None = None,
    *,
    config: ProviderConfig | None = None,
) -> BaseProvider:
    """Return an initialised provider instance.

    Parameters
    ----------
    provider_name:
        Name of the provider to instantiate.  If ``None``, the name is
        read from the environment via :func:`~backend.providers.config.load_config`.
    config:
        Optional pre-built :class:`~backend.providers.config.ProviderConfig`.
        If ``None``, :func:`~backend.providers.config.load_config` is
        called automatically.

    Returns
    -------
    BaseProvider
        A concrete provider instance ready to call ``chat`` or
        ``generate``.

    Raises
    ------
    UnknownProviderError
        If ``provider_name`` is not in :data:`SUPPORTED_PROVIDERS`.
    ValueError
        If the selected provider requires an API key that is not set.
    """
    resolved_config = config or load_config()
    name = (provider_name or resolved_config.provider).lower().strip()

    if name not in _PROVIDER_REGISTRY:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise UnknownProviderError(
            f"Unknown provider {name!r}.  Supported values: {supported}."
        )

    cls = _PROVIDER_REGISTRY[name]
    return cls(config=resolved_config)
