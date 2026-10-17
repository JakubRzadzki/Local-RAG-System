"""Application factory and ASGI entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ollama import AsyncClient

from local_rag_system.config import get_settings
from local_rag_system.database import create_pool, ensure_extension, init_schema
from local_rag_system.exceptions import (
    ConversationNotFoundError,
    DocumentNotFoundError,
    EmptyDocumentError,
    FileTooLargeError,
    InvalidChunkingError,
    ModelNotFoundError,
    OllamaUnavailableError,
    RagError,
    UnsupportedFileTypeError,
    WebSearchError,
)
from local_rag_system.routers import chat, conversations, documents, health, models

logging.basicConfig(level=logging.INFO)

_STATUS_BY_ERROR: dict[type[Exception], int] = {
    DocumentNotFoundError: status.HTTP_404_NOT_FOUND,
    ConversationNotFoundError: status.HTTP_404_NOT_FOUND,
    ModelNotFoundError: status.HTTP_404_NOT_FOUND,
    UnsupportedFileTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    FileTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
    EmptyDocumentError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidChunkingError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    OllamaUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    WebSearchError: status.HTTP_502_BAD_GATEWAY,
}


async def _rag_error_handler(_: Request, exc: Exception) -> JSONResponse:
    code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(status_code=code, content={"detail": str(exc) or type(exc).__name__})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    await ensure_extension(settings)
    pool = create_pool(settings)
    await pool.open()
    await init_schema(pool, settings)
    app.state.pool = pool
    app.state.ollama_client = AsyncClient(host=settings.ollama_host)
    try:
        yield
    finally:
        await pool.close()


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Local RAG System",
        description="Chat with your documents using local Ollama models and pgvector.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RagError, _rag_error_handler)
    for router in (
        health.router,
        models.router,
        documents.router,
        conversations.router,
        chat.router,
    ):
        app.include_router(router)
    return app


app = create_app()


def run() -> None:
    """Run the development server (``local-rag-system`` console script)."""
    uvicorn.run(
        "local_rag_system.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="local_rag_system.event_loop:selector_loop_factory",
    )
