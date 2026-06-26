"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.routes import router
from backend.api.chat_routes import chat_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ORD Experimental Intelligence API",
        version="0.1.0",
        description="Thin FastAPI layer over DuckDB-backed ORD retrieval tools.",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(chat_router)
    return app


app = create_app()
