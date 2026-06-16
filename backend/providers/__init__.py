"""Provider package for the ORD Experimental Intelligence Assistant.

Public API
----------
The only symbols that should be imported by code outside this package:

- :func:`get_provider` — construct a provider from configuration
- :class:`BaseProvider` — type hint for any provider
- :class:`Message` — input message for ``chat``
- :class:`ChatResponse` — response from ``chat``
- :class:`GenerateResponse` — response from ``generate``
- :class:`ProviderConfig` — configuration dataclass
- :func:`load_config` — build config from environment variables
- :data:`SUPPORTED_PROVIDERS` — names of all registered providers
- :exc:`UnknownProviderError` — raised for unrecognised provider names

Concrete provider classes (``OllamaProvider``, ``OpenAIProvider``, …)
are intentionally not re-exported here.  Business logic must use
:func:`get_provider` to remain provider-agnostic.
"""

from .base import BaseProvider, ChatResponse, GenerateResponse, Message
from .config import ProviderConfig, load_config
from .provider_factory import SUPPORTED_PROVIDERS, UnknownProviderError, get_provider

__all__ = [
    "BaseProvider",
    "ChatResponse",
    "GenerateResponse",
    "Message",
    "ProviderConfig",
    "SUPPORTED_PROVIDERS",
    "UnknownProviderError",
    "get_provider",
    "load_config",
]
