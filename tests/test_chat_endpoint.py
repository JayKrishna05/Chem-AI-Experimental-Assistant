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

    def __init__(self, responses: list[str], sleep_time: float = 0.0) -> None:
        self._responses = list(responses)
        self._index = 0
        self.calls: list[list[Message]] = []
        self._sleep_time = sleep_time

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        import time
        if self._sleep_time > 0:
            time.sleep(self._sleep_time)
        self.calls.append(messages)
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
    assert len(events) == 5
    
    e1 = json.loads(events[0].removeprefix("data: "))
    assert e1["type"] == "thinking"
    
    e2 = json.loads(events[1].removeprefix("data: "))
    assert e2["type"] == "tool_selected"
    assert e2["tool"] == "dataset_summary"

    e3 = json.loads(events[2].removeprefix("data: "))
    assert e3["type"] == "formatting"
    
    e4 = json.loads(events[3].removeprefix("data: "))
    assert e4["type"] == "tool_result"
    assert "counts" in e4["result"]
    assert e4["text"] == "The database contains 2.3M reactions."
    
    e5 = json.loads(events[4].removeprefix("data: "))
    assert e5["type"] == "done"


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


def test_chat_endpoint_truncation() -> None:
    mock = ChatMockProvider([
        '{"tool": "dataset_summary", "filters": {}}',
        "Summary here."
    ])
    _PROVIDER_REGISTRY["chat_mock"] = lambda config=None: mock

    # Patch planner result manually for this test via a mock tool
    from backend.planner.planner import Planner
    original_plan = Planner.plan
    def mock_plan(self, message):
        from backend.planner.planner import PlannerResult
        return PlannerResult(
            success=True,
            question=message,
            tool="mock_tool",
            filters={},
            tool_result={"results": [1, 2, 3, 4, 5, 6, 7], "other": "val"},
            raw_llm_response="",
            retried=False
        )
    Planner.plan = mock_plan

    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "test", "provider": "chat_mock"})
        assert response.status_code == 200

        # Verify LLM call received truncated text
        assert len(mock.calls) == 1
        prompt = mock.calls[0][1].content
        assert "Truncated from 7 to 5 items" in prompt
        assert "6," not in prompt
        # But UI gets full data
        events = [line for line in response.text.split("\n\n") if line.strip()]
        result_event = json.loads(events[3].removeprefix("data: "))
        assert len(result_event["result"]["results"]) == 7
    finally:
        Planner.plan = original_plan


def test_chat_endpoint_timeout() -> None:
    mock = ChatMockProvider([
        '{"tool": "dataset_summary", "filters": {}}',
        "Summary."
    ], sleep_time=0.2)
    _PROVIDER_REGISTRY["chat_mock"] = lambda config=None: mock

    from backend.chat import stream
    original_format = stream.format_response
    def fast_timeout_format(provider, planner_result, model=None):
        from backend.chat.formatter import format_response as actual_format
        return actual_format(provider, planner_result, model, timeout=0.01)
    stream.format_response = fast_timeout_format

    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "test", "provider": "chat_mock"})
        assert response.status_code == 200
        
        events = [line for line in response.text.split("\n\n") if line.strip()]
        result_event = json.loads(events[3].removeprefix("data: "))
        assert result_event["text"] == "The response formatting timed out."
    finally:
        stream.format_response = original_format


def main() -> int:
    tests = [
        test_chat_endpoint_success,
        test_chat_endpoint_no_tool,
        test_chat_endpoint_truncation,
        test_chat_endpoint_timeout,
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
