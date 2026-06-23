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
from backend.providers import get_provider, SUPPORTED_PROVIDERS
from backend.api.state import active_models

chat_router = APIRouter()

@chat_router.post("/chat")
def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    """Stream chat events using SSE.

    If the request body doesn't specify a provider/model the active_models
    global (set via POST /models/current) is used as the fallback.
    """
    # --- Resolve planner provider/model/timeout ---
    # planner_provider: request.planner_provider overrides request.provider overrides state
    if not request.planner_provider and request.provider:
        request.planner_provider = request.provider
    if not request.planner_provider:
        request.planner_provider = str(active_models.get("planner_provider", "ollama"))
    if not request.model:
        request.model = active_models.get("planner_model")  # type: ignore[assignment]
    if request.planner_timeout is None:
        request.planner_timeout = float(active_models.get("planner_timeout", 59.0))

    # --- Resolve formatter provider/model/timeout ---
    if not request.formatter_provider:
        request.formatter_provider = str(active_models.get("formatter_provider", "ollama"))
    if not request.formatter_model:
        request.formatter_model = active_models.get("formatter_model")  # type: ignore[assignment]
    if request.formatter_timeout is None:
        request.formatter_timeout = float(active_models.get("formatter_timeout", 59.0))

    return StreamingResponse(
        stream_chat_events(request),
        media_type="text/event-stream",
    )


@chat_router.get("/models", response_model=ModelListResponse)
def list_models(provider: str | None = None) -> ModelListResponse:
    """List available models from the specified provider (default: active planner provider).

    Supports all registered providers.  For providers that require an API key
    (groq, openai, etc.) the key must be set in the environment.
    """
    try:
        provider_name = provider or str(active_models.get("planner_provider", "ollama"))
        prov = get_provider(provider_name)
        models = prov.list_models()
        return ModelListResponse(models=models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/providers")
def list_providers() -> dict:
    """Return the list of supported provider names."""
    return {"providers": sorted(SUPPORTED_PROVIDERS)}


@chat_router.get("/models/current", response_model=CurrentModelsResponse)
def get_current_models() -> CurrentModelsResponse:
    """Return the currently selected providers, models, and timeouts."""
    return CurrentModelsResponse(
        planner_provider=active_models.get("planner_provider"),  # type: ignore[arg-type]
        planner_model=active_models.get("planner_model"),  # type: ignore[arg-type]
        planner_timeout=float(active_models.get("planner_timeout", 59.0)),
        formatter_provider=active_models.get("formatter_provider"),  # type: ignore[arg-type]
        formatter_model=active_models.get("formatter_model"),  # type: ignore[arg-type]
        formatter_timeout=float(active_models.get("formatter_timeout", 59.0)),
    )


@chat_router.post("/models/current", response_model=CurrentModelsResponse)
def set_current_models(req: SetModelsRequest) -> CurrentModelsResponse:
    """Set the active providers, models, or timeouts."""
    if req.planner_provider is not None:
        if req.planner_provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider '{req.planner_provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
            )
        active_models["planner_provider"] = req.planner_provider
    if req.planner_model is not None:
        active_models["planner_model"] = req.planner_model
    if req.planner_timeout is not None:
        t = float(req.planner_timeout)
        if t < 5.0 or t > 600.0:
            raise HTTPException(status_code=400, detail="planner_timeout must be between 5 and 600 seconds")
        active_models["planner_timeout"] = t

    if req.formatter_provider is not None:
        if req.formatter_provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider '{req.formatter_provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
            )
        active_models["formatter_provider"] = req.formatter_provider
    if req.formatter_model is not None:
        active_models["formatter_model"] = req.formatter_model
    if req.formatter_timeout is not None:
        t = float(req.formatter_timeout)
        if t < 5.0 or t > 600.0:
            raise HTTPException(status_code=400, detail="formatter_timeout must be between 5 and 600 seconds")
        active_models["formatter_timeout"] = t

    return CurrentModelsResponse(
        planner_provider=active_models.get("planner_provider"),  # type: ignore[arg-type]
        planner_model=active_models.get("planner_model"),  # type: ignore[arg-type]
        planner_timeout=float(active_models.get("planner_timeout", 59.0)),
        formatter_provider=active_models.get("formatter_provider"),  # type: ignore[arg-type]
        formatter_model=active_models.get("formatter_model"),  # type: ignore[arg-type]
        formatter_timeout=float(active_models.get("formatter_timeout", 59.0)),
    )
