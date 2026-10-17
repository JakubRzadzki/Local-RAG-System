"""API tests with the service layer replaced by fakes (no DB / Ollama needed)."""

import json
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from local_rag_system.dependencies import (
    get_conversation_service,
    get_ingestion_service,
    get_model_service,
    get_rag_service,
)
from local_rag_system.exceptions import (
    ConversationNotFoundError,
    DocumentNotFoundError,
    RagError,
    UnsupportedFileTypeError,
)
from local_rag_system.main import _rag_error_handler
from local_rag_system.repositories.records import (
    ConversationRecord,
    DocumentRecord,
    MessageRecord,
    OllamaModelRecord,
)
from local_rag_system.routers import chat, conversations, documents, health, models
from local_rag_system.schemas.chat import (
    ChatEvent,
    ChatRequest,
    DoneEvent,
    SourceOut,
    SourcesEvent,
    TokenEvent,
)


def _document() -> DocumentRecord:
    return DocumentRecord(1, "a.txt", "text/plain", 10, 2, 800, 100, datetime.now(UTC))


class FakeIngestion:
    async def ingest(self, filename: str, **_: object) -> DocumentRecord:
        if filename.endswith(".exe"):
            raise UnsupportedFileTypeError("nope")
        return _document()

    async def list_documents(self) -> list[DocumentRecord]:
        return [_document()]

    async def delete_document(self, document_id: int) -> None:
        if document_id != 1:
            raise DocumentNotFoundError("missing")


class FakeModels:
    async def list_models(self) -> tuple[list[OllamaModelRecord], bool]:
        chat_model = OllamaModelRecord("llama:8b", 1, "llama", "8B", "Q4", ("completion",))
        embed_model = OllamaModelRecord(
            "nomic-embed-text", 1, "bert", "137M", "F16", ("embedding",)
        )
        return [chat_model, embed_model], True

    @staticmethod
    def supports_chat(model: OllamaModelRecord) -> bool:
        return "completion" in model.capabilities


class FakeRag:
    async def stream_answer(self, _request: ChatRequest) -> AsyncIterator[ChatEvent]:
        yield SourcesEvent(
            sources=[
                SourceOut(
                    index=1,
                    document_id=1,
                    filename="a.txt",
                    chunk_index=0,
                    page=None,
                    score=0.9,
                    content="text",
                )
            ]
        )
        yield TokenEvent(content="Hi")
        yield DoneEvent()


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.add_exception_handler(RagError, _rag_error_handler)
    for router in (health.router, models.router, documents.router, chat.router):
        app.include_router(router)
    app.dependency_overrides[get_ingestion_service] = lambda: FakeIngestion()
    app.dependency_overrides[get_model_service] = lambda: FakeModels()
    app.dependency_overrides[get_rag_service] = lambda: FakeRag()
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_models_flags_chat_support(client: TestClient) -> None:
    body = client.get("/api/models").json()
    assert [m["supports_chat"] for m in body["models"]] == [True, False]
    assert body["embedding_model_installed"] is True


def test_upload_returns_created_document(client: TestClient) -> None:
    response = client.post("/api/documents", files={"file": ("a.txt", b"hello")})
    assert response.status_code == 201
    assert response.json()["filename"] == "a.txt"


def test_upload_unsupported_type_maps_to_415(client: TestClient) -> None:
    response = client.post("/api/documents", files={"file": ("virus.exe", b"x")})
    assert response.status_code == 415


def test_upload_validates_chunk_size(client: TestClient) -> None:
    response = client.post(
        "/api/documents", files={"file": ("a.txt", b"x")}, data={"chunk_size": "5"}
    )
    assert response.status_code == 422


def test_delete_missing_document_is_404(client: TestClient) -> None:
    assert client.delete("/api/documents/1").status_code == 204
    assert client.delete("/api/documents/99").status_code == 404


def test_chat_streams_ndjson_events(client: TestClient) -> None:
    payload = {"model": "llama:8b", "messages": [{"role": "user", "content": "hi"}]}
    response = client.post("/api/chat", json=payload)
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [e["type"] for e in events] == ["sources", "token", "done"]


def test_chat_rejects_conversation_ending_with_assistant(client: TestClient) -> None:
    payload = {"model": "m", "messages": [{"role": "assistant", "content": "hi"}]}
    assert client.post("/api/chat", json=payload).status_code == 422


class FakeConversations:
    async def list_conversations(self) -> list[ConversationRecord]:
        return [_conversation()]

    async def get_with_messages(
        self, conversation_id: int
    ) -> tuple[ConversationRecord, list[MessageRecord]]:
        if conversation_id != 1:
            raise ConversationNotFoundError("missing")
        message = MessageRecord(1, 1, "assistant", "Hi", [], datetime.now(UTC))
        return _conversation(), [message]

    async def rename(self, conversation_id: int, title: str) -> ConversationRecord:
        return _conversation(title)

    async def delete(self, conversation_id: int) -> None:
        if conversation_id != 1:
            raise ConversationNotFoundError("missing")


def _conversation(title: str = "Hello") -> ConversationRecord:
    now = datetime.now(UTC)
    return ConversationRecord(1, title, "llama:8b", now, now)


@pytest.fixture
def conv_client(client: TestClient) -> TestClient:
    app = cast(FastAPI, client.app)
    app.include_router(conversations.router)
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversations()
    return client


def test_conversation_list_and_detail(conv_client: TestClient) -> None:
    assert conv_client.get("/api/conversations").json()[0]["title"] == "Hello"
    detail = conv_client.get("/api/conversations/1").json()
    assert [m["role"] for m in detail["messages"]] == ["assistant"]


def test_conversation_rename_and_validation(conv_client: TestClient) -> None:
    ok = conv_client.patch("/api/conversations/1", json={"title": "New"})
    assert ok.json()["title"] == "New"
    assert conv_client.patch("/api/conversations/1", json={"title": ""}).status_code == 422


def test_conversation_missing_is_404(conv_client: TestClient) -> None:
    assert conv_client.get("/api/conversations/9").status_code == 404
    assert conv_client.delete("/api/conversations/9").status_code == 404
    assert conv_client.delete("/api/conversations/1").status_code == 204
