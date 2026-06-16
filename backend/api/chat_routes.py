"""Chat API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.models import (
    ChatRequest,
    ModelListResponse,
    CurrentModelsResponse,
    SetModelsRequest,
)
from backend.chat.stream import stream_chat_events
from backend.providers import get_provider
from backend.api.state import active_models

chat_router = APIRouter()

@chat_router.post("/chat")
def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    """Stream chat events using SSE."""
    # Inject current active models into request if not explicitly provided
    if not request.model and active_models["planner_model"]:
        request.model = active_models["planner_model"]
    if not request.formatter_model and active_models["formatter_model"]:
        request.formatter_model = active_models["formatter_model"]

    return StreamingResponse(
        stream_chat_events(request),
        media_type="text/event-stream",
    )

@chat_router.get("/models", response_model=ModelListResponse)
def list_models(provider: str | None = None) -> ModelListResponse:
    """List available models from the provider."""
    try:
        prov = get_provider(provider)
        models = prov.list_models()
        return ModelListResponse(models=models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/models/current", response_model=CurrentModelsResponse)
def get_current_models(provider: str | None = None) -> CurrentModelsResponse:
    """Get the currently active models for planner and formatter."""
    prov = get_provider(provider)
    p_model = active_models["planner_model"] or getattr(prov, "_default_model", "unknown")
    f_model = active_models["formatter_model"] or getattr(prov, "_default_model", "unknown")
    return CurrentModelsResponse(planner_model=p_model, formatter_model=f_model)

@chat_router.post("/models/current", response_model=CurrentModelsResponse)
def set_current_models(req: SetModelsRequest, provider: str | None = None) -> CurrentModelsResponse:
    """Set the currently active models."""
    if req.planner_model:
        active_models["planner_model"] = req.planner_model
    if req.formatter_model:
        active_models["formatter_model"] = req.formatter_model
    
    return get_current_models(provider)
