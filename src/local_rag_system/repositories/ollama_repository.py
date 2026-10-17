"""Thin wrapper around the official async ``ollama`` client."""

from collections.abc import AsyncIterator, Mapping, Sequence

import httpx
from ollama import AsyncClient, ResponseError

from local_rag_system.exceptions import ModelNotFoundError, OllamaUnavailableError
from local_rag_system.repositories.records import OllamaModelRecord


class OllamaRepository:
    """All communication with the local Ollama server lives here."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def list_models(self) -> list[OllamaModelRecord]:
        try:
            listing = await self._client.list()
            records: list[OllamaModelRecord] = []
            for model in listing.models:
                if not model.model:
                    continue
                details = model.details
                records.append(
                    OllamaModelRecord(
                        name=model.model,
                        size_bytes=model.size or 0,
                        family=(details.family if details else None) or "",
                        parameter_size=(details.parameter_size if details else None) or "",
                        quantization=(details.quantization_level if details else None) or "",
                        capabilities=await self._capabilities(model.model),
                    )
                )
            return records
        except (httpx.HTTPError, ConnectionError) as exc:
            raise OllamaUnavailableError(str(exc)) from exc

    async def capabilities(self, model: str) -> tuple[str, ...]:
        try:
            return await self._capabilities(model)
        except ResponseError as exc:
            if exc.status_code == 404:
                raise ModelNotFoundError(model) from exc
            raise
        except (httpx.HTTPError, ConnectionError) as exc:
            raise OllamaUnavailableError(str(exc)) from exc

    async def _capabilities(self, model: str) -> tuple[str, ...]:
        info = await self._client.show(model)
        return tuple(info.capabilities or ())

    async def embed(self, model: str, texts: Sequence[str]) -> list[list[float]]:
        try:
            response = await self._client.embed(model=model, input=list(texts))
        except ResponseError as exc:
            if exc.status_code == 404:
                raise ModelNotFoundError(model) from exc
            raise
        except (httpx.HTTPError, ConnectionError) as exc:
            raise OllamaUnavailableError(str(exc)) from exc
        return [list(vector) for vector in response.embeddings]

    async def stream_chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        temperature: float,
        think: bool | None,
    ) -> AsyncIterator[str]:
        """Yield the assistant's answer token by token."""
        try:
            stream = await self._client.chat(
                model=model,
                messages=list(messages),
                stream=True,
                think=think,
                options={"temperature": temperature},
            )
            async for part in stream:
                if part.message.content:
                    yield part.message.content
        except ResponseError as exc:
            if exc.status_code == 404:
                raise ModelNotFoundError(model) from exc
            raise
        except (httpx.HTTPError, ConnectionError) as exc:
            raise OllamaUnavailableError(str(exc)) from exc
