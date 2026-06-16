"""Abstract base class for all LLM provider implementations.

Every concrete provider must implement both ``chat`` and ``generate``.
The interface is intentionally minimal so that the planner layer can
swap providers without touching business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """A single chat message.

    Parameters
    ----------
    role:
        One of ``"system"``, ``"user"``, or ``"assistant"``.
    content:
        The text content of the message.
    """

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    """Normalised response from a provider ``chat`` call.

    Parameters
    ----------
    content:
        The text returned by the model.
    model:
        The model identifier as reported by the provider.
    provider:
        The name of the provider that generated this response.
    raw:
        The full raw response payload from the provider, preserved for
        debugging.  Not part of the public contract.
    """

    content: str
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerateResponse:
    """Normalised response from a provider ``generate`` call.

    Parameters
    ----------
    content:
        The generated text.
    model:
        The model identifier as reported by the provider.
    provider:
        The name of the provider that generated this response.
    raw:
        The full raw response payload from the provider.
    """

    content: str
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Common interface that every LLM provider must implement.

    Subclasses must override ``chat`` and ``generate``.
    They must NOT be instantiated directly.

    Usage
    -----
    Do not import a concrete provider class directly in business logic.
    Use ``provider_factory.get_provider()`` instead so that the
    implementation can be swapped via configuration.
    """

    # Subclasses should set this to a human-readable name, e.g. "ollama".
    provider_name: str = "base"

    @abstractmethod
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
        """Send a list of messages to the model and return the reply.

        Parameters
        ----------
        messages:
            Ordered conversation history.  The last message is typically
            from the user.
        model:
            Override the default model for this call.  If ``None``, the
            provider uses its configured default.
        temperature:
            Sampling temperature (0.0 – 2.0 for most providers).
        max_tokens:
            Upper bound on the number of tokens in the response.
        **kwargs:
            Provider-specific keyword arguments.

        Returns
        -------
        ChatResponse
            Normalised response with ``content``, ``model``, and
            ``provider`` fields.
        """

    @abstractmethod
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
        """Complete a single prompt and return the generated text.

        Parameters
        ----------
        prompt:
            The input text to complete.
        model:
            Override the default model for this call.
        temperature:
            Sampling temperature.
        max_tokens:
            Upper bound on generated tokens.
        **kwargs:
            Provider-specific keyword arguments.

        Returns
        -------
        GenerateResponse
            Normalised response with ``content``, ``model``, and
            ``provider`` fields.
        """

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return a list of available model names for this provider."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(provider_name={self.provider_name!r})"
