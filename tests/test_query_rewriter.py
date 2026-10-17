from collections.abc import Mapping, Sequence

from local_rag_system.exceptions import OllamaUnavailableError
from local_rag_system.schemas.chat import ChatMessage
from local_rag_system.services.query_rewriter import QueryRewriter, needs_rewrite


class FakeOllama:
    def __init__(self, reply: str = "", fail: bool = False) -> None:
        self.reply = reply
        self.fail = fail
        self.calls: list[Sequence[Mapping[str, str]]] = []

    async def chat_once(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        think: bool | None,
        max_tokens: int,
    ) -> str:
        self.calls.append(messages)
        if self.fail:
            raise OllamaUnavailableError("down")
        return self.reply


def _conversation(last: str) -> list[ChatMessage]:
    return [
        ChatMessage(role="user", content="Which planet has the strongest winds?"),
        ChatMessage(role="assistant", content="Neptune."),
        ChatMessage(role="user", content=last),
    ]


def _rewriter(ollama: FakeOllama) -> QueryRewriter:
    return QueryRewriter(ollama)  # type: ignore[arg-type]


def test_only_short_follow_ups_need_rewriting() -> None:
    assert needs_rewrite(_conversation("and the largest?"))
    assert not needs_rewrite(_conversation("x " * 20))
    assert not needs_rewrite(_conversation("hi")[-1:])


async def test_first_question_is_never_rewritten() -> None:
    ollama = FakeOllama(reply="should not be used")
    query = await _rewriter(ollama).rewrite("m", _conversation("hi")[-1:], None)
    assert query == "hi"
    assert ollama.calls == []


async def test_follow_up_is_replaced_by_the_models_standalone_query() -> None:
    ollama = FakeOllama(reply='  "Which planet is the largest?"\n')
    query = await _rewriter(ollama).rewrite("m", _conversation("and the largest?"), None)
    assert query == "Which planet is the largest?"
    # The conversation is passed along so references can be resolved.
    assert "Neptune" in ollama.calls[0][1]["content"]


async def test_failure_falls_back_to_the_original_question() -> None:
    query = await _rewriter(FakeOllama(fail=True)).rewrite("m", _conversation("and more?"), None)
    assert query == "and more?"


async def test_empty_reply_falls_back_to_the_original_question() -> None:
    query = await _rewriter(FakeOllama(reply="  ")).rewrite("m", _conversation("and more?"), None)
    assert query == "and more?"
