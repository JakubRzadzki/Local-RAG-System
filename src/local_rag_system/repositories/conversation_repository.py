"""Persistence of conversations and their messages."""

from collections.abc import Sequence

from psycopg.rows import class_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from local_rag_system.repositories.records import ConversationRecord, MessageRecord

_CONVERSATION_COLUMNS = "id, title, model, created_at, updated_at"
_MESSAGE_COLUMNS = "id, conversation_id, role, content, sources, created_at"


class ConversationRepository:
    """CRUD operations on the ``conversations`` and ``messages`` tables."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def create(self, title: str, model: str) -> ConversationRecord:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(ConversationRecord))
            await cur.execute(
                f"INSERT INTO conversations (title, model) VALUES (%s, %s) "
                f"RETURNING {_CONVERSATION_COLUMNS}",
                (title, model),
            )
            record = await cur.fetchone()
        assert record is not None
        return record

    async def list_all(self) -> list[ConversationRecord]:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(ConversationRecord))
            await cur.execute(
                f"SELECT {_CONVERSATION_COLUMNS} FROM conversations ORDER BY updated_at DESC"
            )
            return await cur.fetchall()

    async def get(self, conversation_id: int) -> ConversationRecord | None:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(ConversationRecord))
            await cur.execute(
                f"SELECT {_CONVERSATION_COLUMNS} FROM conversations WHERE id = %s",
                (conversation_id,),
            )
            return await cur.fetchone()

    async def rename(self, conversation_id: int, title: str) -> ConversationRecord | None:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(ConversationRecord))
            await cur.execute(
                f"UPDATE conversations SET title = %s WHERE id = %s "
                f"RETURNING {_CONVERSATION_COLUMNS}",
                (title, conversation_id),
            )
            return await cur.fetchone()

    async def delete(self, conversation_id: int) -> bool:
        async with self._pool.connection() as conn:
            cur = await conn.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
            return cur.rowcount > 0

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: Sequence[dict[str, object]] = (),
    ) -> None:
        """Append a message and bump the conversation's ``updated_at``."""
        async with self._pool.connection() as conn:
            await conn.execute(
                "INSERT INTO messages (conversation_id, role, content, sources) "
                "VALUES (%s, %s, %s, %s)",
                (conversation_id, role, content, Jsonb(list(sources))),
            )
            await conn.execute(
                "UPDATE conversations SET updated_at = now() WHERE id = %s",
                (conversation_id,),
            )

    async def list_messages(self, conversation_id: int) -> list[MessageRecord]:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(MessageRecord))
            await cur.execute(
                f"SELECT {_MESSAGE_COLUMNS} FROM messages WHERE conversation_id = %s ORDER BY id",
                (conversation_id,),
            )
            return await cur.fetchall()
