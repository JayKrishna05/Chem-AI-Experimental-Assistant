"""Chat API routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.api.models import ChatRequest
from backend.chat.stream import stream_chat_events

chat_router = APIRouter()

@chat_router.post("/chat")
def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    """Stream chat events using SSE."""
    return StreamingResponse(
        stream_chat_events(request),
        media_type="text/event-stream",
    )
