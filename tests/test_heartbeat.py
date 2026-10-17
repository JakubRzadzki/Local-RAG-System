import asyncio
from collections.abc import AsyncIterator

from local_rag_system.schemas.chat import ChatEvent, DoneEvent, PingEvent, TokenEvent
from local_rag_system.services.rag_service import with_heartbeat


async def _slow_events() -> AsyncIterator[ChatEvent]:
    yield TokenEvent(content="a")
    await asyncio.sleep(0.35)
    yield DoneEvent()


async def test_pings_are_emitted_while_waiting() -> None:
    types = [event.type async for event in with_heartbeat(_slow_events(), 0.1)]
    assert types[0] == "token"
    assert types[-1] == "done"
    assert types.count("ping") >= 2


async def test_fast_stream_has_no_pings() -> None:
    async def fast() -> AsyncIterator[ChatEvent]:
        yield TokenEvent(content="a")
        yield DoneEvent()

    events = [e async for e in with_heartbeat(fast(), 5)]
    assert not any(isinstance(e, PingEvent) for e in events)
    assert len(events) == 2


async def test_abandoned_stream_runs_the_generators_cleanup() -> None:
    cleaned = asyncio.Event()

    async def events() -> AsyncIterator[ChatEvent]:
        try:
            yield TokenEvent(content="a")
            await asyncio.sleep(10)
            yield DoneEvent()
        finally:
            cleaned.set()  # e.g. saving the partial answer

    stream = with_heartbeat(events(), 0.05)
    assert (await anext(stream)).type == "token"
    await stream.aclose()  # what Starlette does when the client disconnects

    assert cleaned.is_set()
