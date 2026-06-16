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
def get_current_models() -> CurrentModelsResponse:
    """Return the currently selected models and timeout for planner and formatter."""
    return CurrentModelsResponse(
        planner_model=active_models.get("planner_model"),
        formatter_model=active_models.get("formatter_model"),
        formatter_timeout=active_models.get("formatter_timeout", 59.0),
    )

@chat_router.post("/models/current", response_model=CurrentModelsResponse)
def set_current_models(req: SetModelsRequest) -> CurrentModelsResponse:
    """Set the currently active models or timeout."""
    if req.planner_model is not None:
        active_models["planner_model"] = req.planner_model
    if req.formatter_model is not None:
        active_models["formatter_model"] = req.formatter_model
    if req.formatter_timeout is not None:
        timeout = float(req.formatter_timeout)
        if timeout < 5.0 or timeout > 300.0:
            raise HTTPException(status_code=400, detail="Timeout must be between 5 and 300 seconds")
        active_models["formatter_timeout"] = timeout
        
    return CurrentModelsResponse(
        planner_model=active_models.get("planner_model"),
        formatter_model=active_models.get("formatter_model"),
        formatter_timeout=active_models.get("formatter_timeout", 59.0),
    )
