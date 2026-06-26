"""Tests for the provider abstraction layer.

Structure
---------
Unit tests (always run):
  - Base class interface contract (abstract methods raise TypeError)
  - Config loading from environment variables
  - Factory: known providers, unknown provider, env-driven selection
  - Stub providers raise NotImplementedError (with correct key set)
  - OllamaProvider HTTP request construction (mock HTTP server)
  - OllamaProvider error handling (connection refused, bad JSON)

Integration tests (skipped when Ollama is unreachable):
  - Live OllamaProvider.chat round-trip
  - Live OllamaProvider.generate round-trip

Run with:
    python scripts/test_providers.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.providers import (  # noqa: E402
    SUPPORTED_PROVIDERS,
    BaseProvider,
    ChatResponse,
    GenerateResponse,
    Message,
    ProviderConfig,
    UnknownProviderError,
    get_provider,
    load_config,
)
from backend.providers.config import (  # noqa: E402
    _DEFAULT_OLLAMA_BASE_URL,
    _DEFAULT_PLANNER_MODEL,
    _DEFAULT_PROVIDER,
)
from backend.providers.ollama_provider import (  # noqa: E402
    OllamaConnectionError,
    OllamaProvider,
    OllamaResponseError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides: Any) -> ProviderConfig:
    """Build a ProviderConfig with safe test defaults."""
    base = ProviderConfig(
        provider=overrides.pop("provider", "ollama"),
        planner_model=overrides.pop("planner_model", "test-model"),
        ollama_base_url=overrides.pop("ollama_base_url", "http://localhost:11434"),
        openai_api_key=overrides.pop("openai_api_key", None),
        anthropic_api_key=overrides.pop("anthropic_api_key", None),
        gemini_api_key=overrides.pop("gemini_api_key", None),
        _analysis_model_override=overrides.pop("_analysis_model_override", None),
    )
    return base


class _MockOllamaHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that mimics Ollama chat and generate endpoints."""

    # The canned responses are set by test fixtures via class attributes.
    chat_response: dict[str, Any] = {
        "model": "test-model",
        "message": {"role": "assistant", "content": "Hello from mock Ollama!"},
    }
    generate_response: dict[str, Any] = {
        "model": "test-model",
        "response": "Generated text from mock Ollama.",
    }

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/api/chat":
            data = json.dumps(self.__class__.chat_response).encode()
        elif self.path == "/api/generate":
            data = json.dumps(self.__class__.generate_response).encode()
        else:
            self.send_response(404)
            self.end_headers()
            return

        # Store last received body so tests can inspect it.
        self.__class__.last_body = body

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args: Any) -> None:  # noqa: ANN002
        pass  # Suppress HTTP log noise in test output.


class _MockOllamaServer:
    """Context manager that starts a local HTTP server mimicking Ollama."""

    def __init__(self) -> None:
        self.server: HTTPServer | None = None
        self.base_url: str = ""

    def __enter__(self) -> _MockOllamaServer:
        self.server = HTTPServer(("127.0.0.1", 0), _MockOllamaHandler)
        port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{port}"
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        if self.server:
            self.server.shutdown()


# ---------------------------------------------------------------------------
# Test: BaseProvider interface
# ---------------------------------------------------------------------------


def test_base_provider_is_abstract() -> None:
    """BaseProvider cannot be instantiated directly."""
    try:
        BaseProvider()  # type: ignore[abstract]
        raise AssertionError("Expected TypeError when instantiating BaseProvider")
    except TypeError:
        pass  # Expected


def test_base_provider_has_chat_and_generate() -> None:
    """BaseProvider declares chat and generate as abstract methods."""
    assert "chat" in BaseProvider.__abstractmethods__
    assert "generate" in BaseProvider.__abstractmethods__


# ---------------------------------------------------------------------------
# Test: ProviderConfig / load_config
# ---------------------------------------------------------------------------


def test_load_config_defaults() -> None:
    """load_config returns correct defaults when no env vars are set."""
    clean_env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("ORD_")
    }
    with patch.dict(os.environ, clean_env, clear=True):
        cfg = load_config()

    assert cfg.provider == _DEFAULT_PROVIDER
    assert cfg.planner_model == _DEFAULT_PLANNER_MODEL
    assert cfg.analysis_model == _DEFAULT_PLANNER_MODEL  # fallback
    assert cfg.ollama_base_url == _DEFAULT_OLLAMA_BASE_URL
    assert cfg.openai_api_key is None
    assert cfg.anthropic_api_key is None
    assert cfg.gemini_api_key is None


def test_load_config_from_env() -> None:
    """load_config picks up all ORD_* environment variables."""
    env = {
        "ORD_PROVIDER": "openai",
        "ORD_PLANNER_MODEL": "gpt-4o",
        "ORD_ANALYSIS_MODEL": "gpt-4o-mini",
        "ORD_OLLAMA_BASE_URL": "http://custom:9999",
        "ORD_OPENAI_API_KEY": "sk-test",
        "ORD_ANTHROPIC_API_KEY": "ant-test",
        "ORD_GEMINI_API_KEY": "gem-test",
    }
    with patch.dict(os.environ, env):
        cfg = load_config()

    assert cfg.provider == "openai"
    assert cfg.planner_model == "gpt-4o"
    assert cfg.analysis_model == "gpt-4o-mini"
    assert cfg.ollama_base_url == "http://custom:9999"
    assert cfg.openai_api_key == "sk-test"
    assert cfg.anthropic_api_key == "ant-test"
    assert cfg.gemini_api_key == "gem-test"


def test_config_analysis_model_fallback() -> None:
    """analysis_model falls back to planner_model when not explicitly set."""
    cfg = _make_config(planner_model="my-planner")
    assert cfg.analysis_model == "my-planner"


def test_config_analysis_model_override() -> None:
    """analysis_model uses override when provided."""
    cfg = _make_config(planner_model="planner", _analysis_model_override="analyst")
    assert cfg.analysis_model == "analyst"
    assert cfg.planner_model == "planner"


def test_ollama_base_url_trailing_slash_stripped() -> None:
    """Trailing slashes in ORD_OLLAMA_BASE_URL are stripped."""
    with patch.dict(os.environ, {"ORD_OLLAMA_BASE_URL": "http://localhost:11434/"}):
        cfg = load_config()
    assert not cfg.ollama_base_url.endswith("/")


# ---------------------------------------------------------------------------
# Test: factory — SUPPORTED_PROVIDERS
# ---------------------------------------------------------------------------


def test_supported_providers_contains_all() -> None:
    """All four providers are registered."""
    assert SUPPORTED_PROVIDERS == {"ollama", "openai", "anthropic", "gemini"}


def test_get_provider_unknown_raises() -> None:
    """get_provider raises UnknownProviderError for unrecognised names."""
    cfg = _make_config(provider="unknown-llm")
    try:
        get_provider("unknown-llm", config=cfg)
        raise AssertionError("Expected UnknownProviderError")
    except UnknownProviderError as exc:
        assert "unknown-llm" in str(exc)


def test_get_provider_ollama_returns_ollama_provider() -> None:
    """get_provider('ollama') returns an OllamaProvider instance."""
    cfg = _make_config(provider="ollama")
    provider = get_provider("ollama", config=cfg)
    assert provider.provider_name == "ollama"
    assert isinstance(provider, OllamaProvider)


def test_get_provider_uses_config_provider_when_name_is_none() -> None:
    """get_provider() without explicit name uses config.provider."""
    cfg = _make_config(provider="ollama")
    provider = get_provider(None, config=cfg)
    assert provider.provider_name == "ollama"


def test_get_provider_env_driven() -> None:
    """get_provider() respects ORD_PROVIDER env var when no name is passed."""
    with patch.dict(os.environ, {"ORD_PROVIDER": "ollama"}):
        provider = get_provider()
    assert provider.provider_name == "ollama"


# ---------------------------------------------------------------------------
# Test: stub providers
# ---------------------------------------------------------------------------


def test_openai_stub_raises_without_api_key() -> None:
    """OpenAIProvider raises ValueError when api key is not set."""
    cfg = _make_config(provider="openai", openai_api_key=None)
    try:
        get_provider("openai", config=cfg)
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "ORD_OPENAI_API_KEY" in str(exc)


def test_openai_stub_raises_not_implemented() -> None:
    """OpenAI chat/generate raise NotImplementedError."""
    from backend.providers.openai_provider import OpenAIProvider

    cfg = _make_config(openai_api_key="sk-fake")
    provider = OpenAIProvider(config=cfg)
    msg = Message(role="user", content="hello")

    try:
        provider.chat([msg])
        raise AssertionError("Expected NotImplementedError from chat")
    except NotImplementedError:
        pass

    try:
        provider.generate("hello")
        raise AssertionError("Expected NotImplementedError from generate")
    except NotImplementedError:
        pass


def test_anthropic_stub_raises_without_api_key() -> None:
    """AnthropicProvider raises ValueError when api key is not set."""
    cfg = _make_config(provider="anthropic", anthropic_api_key=None)
    try:
        get_provider("anthropic", config=cfg)
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "ORD_ANTHROPIC_API_KEY" in str(exc)


def test_anthropic_stub_raises_not_implemented() -> None:
    """Anthropic chat/generate raise NotImplementedError."""
    from backend.providers.anthropic_provider import AnthropicProvider

    cfg = _make_config(anthropic_api_key="ant-fake")
    provider = AnthropicProvider(config=cfg)
    msg = Message(role="user", content="hello")

    try:
        provider.chat([msg])
        raise AssertionError("Expected NotImplementedError from chat")
    except NotImplementedError:
        pass

    try:
        provider.generate("hello")
        raise AssertionError("Expected NotImplementedError from generate")
    except NotImplementedError:
        pass


def test_gemini_stub_raises_without_api_key() -> None:
    """GeminiProvider raises ValueError when api key is not set."""
    cfg = _make_config(provider="gemini", gemini_api_key=None)
    try:
        get_provider("gemini", config=cfg)
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "ORD_GEMINI_API_KEY" in str(exc)


def test_gemini_stub_raises_not_implemented() -> None:
    """Gemini chat/generate raise NotImplementedError."""
    from backend.providers.gemini_provider import GeminiProvider

    cfg = _make_config(gemini_api_key="gem-fake")
    provider = GeminiProvider(config=cfg)
    msg = Message(role="user", content="hello")

    try:
        provider.chat([msg])
        raise AssertionError("Expected NotImplementedError from chat")
    except NotImplementedError:
        pass

    try:
        provider.generate("hello")
        raise AssertionError("Expected NotImplementedError from generate")
    except NotImplementedError:
        pass


# ---------------------------------------------------------------------------
# Test: OllamaProvider — unit tests with mock HTTP server
# ---------------------------------------------------------------------------


def test_ollama_chat_sends_correct_request() -> None:
    """OllamaProvider.chat sends the right JSON body and parses the response."""
    with _MockOllamaServer() as srv:
        cfg = _make_config(ollama_base_url=srv.base_url, planner_model="test-model")
        provider = OllamaProvider(config=cfg)

        messages = [
            Message(role="system", content="You are a chemistry assistant."),
            Message(role="user", content="What is a Suzuki reaction?"),
        ]
        response = provider.chat(messages)

    assert isinstance(response, ChatResponse)
    assert response.content == "Hello from mock Ollama!"
    assert response.model == "test-model"
    assert response.provider == "ollama"

    sent = _MockOllamaHandler.last_body
    assert sent["model"] == "test-model"
    assert sent["stream"] is False
    assert len(sent["messages"]) == 2
    assert sent["messages"][0]["role"] == "system"
    assert sent["messages"][1]["role"] == "user"


def test_ollama_generate_sends_correct_request() -> None:
    """OllamaProvider.generate sends the right JSON body and parses the response."""
    with _MockOllamaServer() as srv:
        cfg = _make_config(ollama_base_url=srv.base_url, planner_model="test-model")
        provider = OllamaProvider(config=cfg)

        response = provider.generate("Describe a Buchwald-Hartwig reaction.")

    assert isinstance(response, GenerateResponse)
    assert response.content == "Generated text from mock Ollama."
    assert response.model == "test-model"
    assert response.provider == "ollama"

    sent = _MockOllamaHandler.last_body
    assert sent["model"] == "test-model"
    assert sent["stream"] is False
    assert "prompt" in sent


def test_ollama_chat_passes_options() -> None:
    """Temperature and max_tokens are forwarded as Ollama options."""
    with _MockOllamaServer() as srv:
        cfg = _make_config(ollama_base_url=srv.base_url)
        provider = OllamaProvider(config=cfg)
        provider.chat(
            [Message(role="user", content="hi")],
            temperature=0.1,
            max_tokens=64,
        )

    sent = _MockOllamaHandler.last_body
    assert sent["options"]["temperature"] == 0.1
    assert sent["options"]["num_predict"] == 64


def test_ollama_model_override() -> None:
    """Per-call model override takes precedence over default model."""
    with _MockOllamaServer() as srv:
        cfg = _make_config(
            ollama_base_url=srv.base_url, planner_model="default-model"
        )
        provider = OllamaProvider(config=cfg)
        provider.chat(
            [Message(role="user", content="hi")],
            model="override-model",
        )

    sent = _MockOllamaHandler.last_body
    assert sent["model"] == "override-model"


def test_ollama_connection_error() -> None:
    """OllamaProvider raises OllamaConnectionError when server is unreachable."""
    cfg = _make_config(ollama_base_url="http://127.0.0.1:19999")
    provider = OllamaProvider(config=cfg, timeout=2)

    try:
        provider.chat([Message(role="user", content="hello")])
        raise AssertionError("Expected OllamaConnectionError")
    except OllamaConnectionError:
        pass


def test_ollama_bad_json_response() -> None:
    """OllamaProvider raises OllamaResponseError for non-JSON server responses."""

    class _BadJsonHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            data = b"not-json!!!"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), _BadJsonHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        provider = OllamaProvider(
            base_url=f"http://127.0.0.1:{port}",
            config=_make_config(),
        )
        try:
            provider.chat([Message(role="user", content="hi")])
            raise AssertionError("Expected OllamaResponseError")
        except OllamaResponseError:
            pass
    finally:
        server.shutdown()


def test_ollama_is_reachable_false_when_nothing_listening() -> None:
    """is_reachable() returns False when nothing is running on the target port."""
    provider = OllamaProvider(
        base_url="http://127.0.0.1:19998",
        config=_make_config(),
        timeout=1,
    )
    assert provider.is_reachable() is False


# ---------------------------------------------------------------------------
# Test: OllamaProvider — live integration (skipped unless Ollama is up)
# ---------------------------------------------------------------------------


def _live_ollama_provider() -> OllamaProvider | None:
    """Return a live OllamaProvider if reachable, else None."""
    provider = OllamaProvider(config=load_config())
    return provider if provider.is_reachable() else None


def test_ollama_live_chat() -> None:
    """Integration: OllamaProvider.chat with a real Ollama server."""
    provider = _live_ollama_provider()
    if provider is None:
        print("    SKIP  test_ollama_live_chat (Ollama not reachable)")
        return

    messages = [
        Message(role="system", content="Reply with exactly one word."),
        Message(role="user", content="Say hello."),
    ]
    response = provider.chat(messages, max_tokens=10)
    assert isinstance(response, ChatResponse)
    assert len(response.content) > 0
    assert response.provider == "ollama"


def test_ollama_live_generate() -> None:
    """Integration: OllamaProvider.generate with a real Ollama server."""
    provider = _live_ollama_provider()
    if provider is None:
        print("    SKIP  test_ollama_live_generate (Ollama not reachable)")
        return

    response = provider.generate("Complete: The sky is", max_tokens=5)
    assert isinstance(response, GenerateResponse)
    assert len(response.content) > 0
    assert response.provider == "ollama"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> int:
    tests = [
        # BaseProvider interface
        test_base_provider_is_abstract,
        test_base_provider_has_chat_and_generate,
        # Config
        test_load_config_defaults,
        test_load_config_from_env,
        test_config_analysis_model_fallback,
        test_config_analysis_model_override,
        test_ollama_base_url_trailing_slash_stripped,
        # Factory
        test_supported_providers_contains_all,
        test_get_provider_unknown_raises,
        test_get_provider_ollama_returns_ollama_provider,
        test_get_provider_uses_config_provider_when_name_is_none,
        test_get_provider_env_driven,
        # Stubs
        test_openai_stub_raises_without_api_key,
        test_openai_stub_raises_not_implemented,
        test_anthropic_stub_raises_without_api_key,
        test_anthropic_stub_raises_not_implemented,
        test_gemini_stub_raises_without_api_key,
        test_gemini_stub_raises_not_implemented,
        # Ollama unit tests (mock server)
        test_ollama_chat_sends_correct_request,
        test_ollama_generate_sends_correct_request,
        test_ollama_chat_passes_options,
        test_ollama_model_override,
        test_ollama_connection_error,
        test_ollama_bad_json_response,
        test_ollama_is_reachable_false_when_nothing_listening,
        # Ollama live integration (skipped if not reachable)
        test_ollama_live_chat,
        test_ollama_live_generate,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {test.__name__}: {exc}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
