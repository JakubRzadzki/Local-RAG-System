"""RagService with fake collaborators: score threshold and persistence."""

from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import UTC, datetime

from local_rag_system.repositories.records import ConversationRecord, RetrievedChunk
from local_rag_system.schemas.chat import ChatMessage, ChatRequest, SourcesEvent
from local_rag_system.services.rag_service import RagService


def _chunk(index: int, score: float) -> RetrievedChunk:
    return RetrievedChunk(index, 1, "a.txt", index, None, f"text {index}", score)


class FakeChunks:
    async def search(
        self, embedding: list[float], top_k: int, document_ids: Sequence[int] | None = None
    ) -> list[RetrievedChunk]:
        return [_chunk(0, 0.8), _chunk(1, 0.55)]


class FakeConversations:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def create(self, title: str, model: str) -> ConversationRecord:
        now = datetime.now(UTC)
        return ConversationRecord(1, title, model, now, now)

    async def add_message(
        self, conversation_id: int, role: str, content: str, sources: object = ()
    ) -> None:
        self.messages.append((role, content))


class FakeOllama:
    async def capabilities(self, model: str) -> tuple[str, ...]:
        return ()

    async def stream_chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        temperature: float,
        think: bool | None,
    ) -> AsyncIterator[str]:
        yield "Hi"
        yield " there"

    async def chat_once(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        think: bool | None,
        max_tokens: int,
    ) -> str:
        return "Which planet is the largest?"


class FakeEmbeddings:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def embed_query(self, query: str) -> list[float]:
        self.queries.append(query)
        return [0.0]


def _service(
    conversations: FakeConversations,
    min_score: float,
    embeddings: FakeEmbeddings | None = None,
) -> RagService:
    return RagService(
        FakeChunks(),  # type: ignore[arg-type]
        conversations,  # type: ignore[arg-type]
        FakeOllama(),  # type: ignore[arg-type]
        embeddings or FakeEmbeddings(),  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        min_score,
    )


def _request() -> ChatRequest:
    return ChatRequest(model="m", messages=[ChatMessage(role="user", content="hello?")])


async def test_chunks_below_the_minimum_score_are_dropped() -> None:
    service = _service(FakeConversations(), min_score=0.6)
    events = [e async for e in service.stream_answer(_request())]
    sources = next(e for e in events if isinstance(e, SourcesEvent)).sources
    assert [s.chunk_index for s in sources] == [0]


async def test_nothing_is_dropped_when_threshold_is_zero() -> None:
    service = _service(FakeConversations(), min_score=0.0)
    events = [e async for e in service.stream_answer(_request())]
    sources = next(e for e in events if isinstance(e, SourcesEvent)).sources
    assert len(sources) == 2


async def test_user_message_and_full_answer_are_saved() -> None:
    conversations = FakeConversations()
    service = _service(conversations, min_score=0.6)
    _ = [e async for e in service.stream_answer(_request())]
    assert conversations.messages == [("user", "hello?"), ("assistant", "Hi there")]


async def test_follow_up_retrieves_with_the_rewritten_query_but_saves_the_original() -> None:
    embeddings, conversations = FakeEmbeddings(), FakeConversations()
    request = ChatRequest(
        model="m",
        messages=[
            ChatMessage(role="user", content="Which planet has the strongest winds?"),
            ChatMessage(role="assistant", content="Neptune."),
            ChatMessage(role="user", content="and the largest?"),
        ],
    )

    _ = [e async for e in _service(conversations, 0.0, embeddings).stream_answer(request)]

    assert embeddings.queries == ["Which planet is the largest?"]
    assert conversations.messages[0] == ("user", "and the largest?")


async def test_first_question_is_embedded_unchanged() -> None:
    embeddings = FakeEmbeddings()
    service = _service(FakeConversations(), 0.0, embeddings)

    _ = [e async for e in service.stream_answer(_request())]

    assert embeddings.queries == ["hello?"]
