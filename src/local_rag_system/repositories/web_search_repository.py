"""Web search through DuckDuckGo (no API key required)."""

import asyncio

from ddgs import DDGS

from local_rag_system.exceptions import WebSearchError
from local_rag_system.repositories.records import WebResult


class WebSearchRepository:
    """Runs web searches; the ``ddgs`` client is synchronous, so it runs in a thread."""

    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    async def search(self, query: str, max_results: int) -> list[WebResult]:
        try:
            raw = await asyncio.to_thread(self._search_sync, query, max_results)
        except Exception as exc:
            raise WebSearchError(str(exc) or "web search failed") from exc
        return [
            WebResult(title=r.get("title", ""), url=r.get("href", ""), snippet=r.get("body", ""))
            for r in raw
            if r.get("href")
        ]

    def _search_sync(self, query: str, max_results: int) -> list[dict[str, str]]:
        return list(DDGS(timeout=self._timeout).text(query, max_results=max_results))
