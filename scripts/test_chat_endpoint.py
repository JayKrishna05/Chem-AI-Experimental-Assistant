"""Tests for the POST /chat endpoint with SSE streaming."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.main import app  # noqa: E402
from backend.providers.base import BaseProvider, ChatResponse, Message  # noqa: E402
from backend.providers.provider_factory import _PROVIDER_REGISTRY  # noqa: E402


class ChatMockProvider(BaseProvider):
    provider_name = "chat_mock"

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        content = self._responses[self._index]
        self._index += 1
        return ChatResponse(content=content, model="mock", provider="chat_mock")

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        raise NotImplementedError


def test_chat_endpoint_success() -> None:
    _PROVIDER_REGISTRY["chat_mock"] = lambda config=None: ChatMockProvider([
        '{"tool": "dataset_summary", "filters": {}}',  # Planner intent
        "The database contains 2.3M reactions."        # Formatter NL response
    ])

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "Summarise the database", "provider": "chat_mock"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    events = [line for line in response.text.split("\n\n") if line.strip()]
    assert len(events) == 4
    
    e1 = json.loads(events[0].removeprefix("data: "))
    assert e1["type"] == "thinking"
    
    e2 = json.loads(events[1].removeprefix("data: "))
    assert e2["type"] == "tool_selected"
    assert e2["tool"] == "dataset_summary"
    
    e3 = json.loads(events[2].removeprefix("data: "))
    assert e3["type"] == "tool_result"
    assert "counts" in e3["result"]
    assert e3["text"] == "The database contains 2.3M reactions."
    
    e4 = json.loads(events[3].removeprefix("data: "))
    assert e4["type"] == "done"


def test_chat_endpoint_no_tool() -> None:
    _PROVIDER_REGISTRY["chat_mock"] = lambda config=None: ChatMockProvider([
        '{"tool": "__none__", "filters": {}}',  # Planner intent
    ])

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "What is the capital of France?", "provider": "chat_mock"}
    )
    
    assert response.status_code == 200
    
    events = [line for line in response.text.split("\n\n") if line.strip()]
    assert len(events) == 3
    
    e1 = json.loads(events[0].removeprefix("data: "))
    assert e1["type"] == "thinking"
    
    e2 = json.loads(events[1].removeprefix("data: "))
    assert e2["type"] == "no_tool"
    assert e2["question"] == "What is the capital of France?"
    
    e3 = json.loads(events[2].removeprefix("data: "))
    assert e3["type"] == "done"


def main() -> int:
    tests = [
        test_chat_endpoint_success,
        test_chat_endpoint_no_tool,
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
