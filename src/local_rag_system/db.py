import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

DSN = "postgresql://postgres:postgres@localhost:5432/rag"
EMBED_DIM = 768 # nomic-embed-text

def _configure(conn : psycopg.Connection) -> None:
    register_vector(conn)

def init_db() -> None:
    # the extension must exist before the pool registers the vector type
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    pool.open()
    with pool.connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )""")

        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INT NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR({EMBED_DIM}) NOT NULL
            )""")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks USING hnsw (embedding vector_cosine_ops)
        """)

pool = ConnectionPool(DSN, min_size=1, max_size=10, configure=_configure, open=False)
