# Local RAG System

Chat with your own documents, **100% locally**. Upload TXT / Markdown / PDF files, pick any
language model you have installed in [Ollama](https://ollama.com), and get streamed answers
with the exact source chunks that were used (document, chunk number, PDF page, similarity).

The RAG pipeline is written from scratch: **no LangChain, no LlamaIndex** — just Python, the
official `ollama` client and PostgreSQL + `pgvector`.

## Features

- ChatGPT-style UI with token-by-token streaming and Markdown rendering
- Model picker populated from your **locally installed** Ollama models (embedding-only models are filtered out automatically)
- Tunable per request: `temperature`, `top_k`; tunable per upload: `chunk_size`, `chunk_overlap`
- Source inspector under every answer: filename, chunk index, page (PDF), cosine-similarity score and the chunk text
- Restrict a conversation to selected documents
- **Saved chat history**: conversations are stored in PostgreSQL; reopen, rename or delete them from the *Chats* tab (partial answers are kept when you press stop)
- **Document preview**: inspect every stored chunk of a file, and jump from a cited source straight to its highlighted chunk
- The assistant knows how the app works (built-in guide in `services/app_guide.py`), so you can simply ask *"How does this application work?"*
- Paragraph-aware chunking with overlap; per-page chunking for PDFs
- Typed end to end: Pydantic on the backend, strict TypeScript (no `any`) on the frontend

## Architecture

```
React + TS (Vite)  ──HTTP/NDJSON──►  FastAPI
                                       │
   routers/       HTTP only: routing, status codes
      │
   services/      business logic: chunking, extraction, ingestion, prompt, RAG orchestration
      │
   repositories/  data access: pgvector (documents, chunks) and the Ollama client
      │
   PostgreSQL + pgvector            Ollama (embeddings + chat)
```

```
src/local_rag_system/
├── config.py            settings (env vars prefixed RAG_)
├── database.py          async pool + schema
├── dependencies.py      dependency injection wiring
├── exceptions.py        domain errors → HTTP status in main.py
├── main.py              app factory
├── routers/             health, models, documents, chat
├── schemas/             Pydantic request/response DTOs
├── services/            chunking, text extraction, embedding, ingestion, prompt builder, RAG
└── repositories/        document_repository, chunk_repository, ollama_repository
frontend/src/
├── api/client.ts        typed fetch + NDJSON stream reader
├── hooks/               useChat, useModels, useDocuments, useLocalStorage
└── components/          Sidebar, UploadZone, DocumentList, ModelSelect, SettingsPanel,
                         ChatWindow, MessageBubble, SourceList, Composer
sample_docs/             ready-to-use test documents (PL + EN; TXT, MD, PDF)
tests/                   pytest suite
```

**RAG flow:** upload → extract text → chunk → embed (`nomic-embed-text`) → store vectors in
pgvector (HNSW index). On a question: embed the query → cosine top-k search → build a prompt
with numbered context → stream the answer from the chosen model. The model is instructed to
cite excerpts as `[1]`, `[2]`, … and to say so when the context does not contain the answer.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (for PostgreSQL with pgvector)
- [Ollama](https://ollama.com) running locally

### Ollama models

```bash
ollama pull nomic-embed-text   # required: embeddings (768 dimensions)
ollama pull gemma3:4b          # any chat model works; this is just an example
```

Any installed model with the `completion` capability shows up in the UI model picker.
If you change the embedding model, set `RAG_EMBEDDING_MODEL` / `RAG_EMBEDDING_DIM` and
recreate the `chunks` table (vector size is fixed per column).

## Running

```bash
# 1. database
docker compose up -d

# 2. backend (http://127.0.0.1:8000, docs at /docs)
uv sync
uv run local-rag-system

# 3. frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```

Then drag the files from `sample_docs/` into the sidebar and ask, for example:

- *Ile dni urlopu przysługuje pracownikowi NovaTech?*
- *Which planet has the strongest winds?*
- *Which command runs tests until the first failure?*

> **Windows note:** psycopg's async mode needs a `SelectorEventLoop`. `uv run local-rag-system`
> configures this for you. If you start uvicorn manually, add
> `--loop local_rag_system.event_loop:selector_loop_factory`.

### Configuration

Environment variables (or a `.env` file), all optional:

| Variable | Default |
|---|---|
| `RAG_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/rag` |
| `RAG_OLLAMA_HOST` | `http://localhost:11434` |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` |
| `RAG_EMBEDDING_DIM` | `768` |
| `RAG_DEFAULT_CHUNK_SIZE` / `RAG_DEFAULT_CHUNK_OVERLAP` | `800` / `100` |
| `RAG_MAX_UPLOAD_BYTES` | `20971520` (20 MB) |
| `RAG_CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` |

## API

Interactive docs: `http://127.0.0.1:8000/docs`.

| Method & path | Description |
|---|---|
| `GET /api/health` | Liveness probe. |
| `GET /api/models` | Installed Ollama models with `capabilities` and `supports_chat`; also reports whether the embedding model is installed. |
| `GET /api/documents` | List indexed documents. |
| `POST /api/documents` | Multipart upload: `file` (TXT/MD/PDF), optional `chunk_size` (100–4000), `chunk_overlap` (0–1000). Returns `201` with the document. Errors: `413` too large, `415` unsupported type, `422` no text / invalid chunking, `503` Ollama down. |
| `GET /api/documents/{id}/preview` | Document metadata plus all its chunks (`chunk_index`, `page`, `content`) in reading order. |
| `DELETE /api/documents/{id}` | Delete a document and its chunks (`204`, or `404`). |
| `GET /api/conversations` | Saved conversations, most recently active first. |
| `GET /api/conversations/{id}` | A conversation with its messages and their sources. |
| `PATCH /api/conversations/{id}` | Rename: `{"title": "..."}`. |
| `DELETE /api/conversations/{id}` | Delete a conversation (`204`, or `404`). |
| `POST /api/chat` | Streaming RAG answer (see below). |

### `POST /api/chat`

```json
{
  "model": "gemma3:4b",
  "messages": [{ "role": "user", "content": "What is top_k?" }],
  "options": { "temperature": 0.2, "top_k": 4, "document_ids": null },
  "conversation_id": null
}
```

The response is `application/x-ndjson`, one JSON event per line:

```jsonl
{"type":"conversation","id":1,"title":"What is top_k?"}
{"type":"sources","sources":[{"index":1,"document_id":3,"filename":"rag-explained.md","chunk_index":2,"page":null,"score":0.83,"content":"…"}]}
{"type":"token","content":"top"}
{"type":"token","content":"_k"}
{"type":"done"}
```

Failures after streaming has started are reported in-band as `{"type":"error","message":"…"}`.
The first event announces the conversation (new when `conversation_id` is `null`). The client sends the message history; the server stores the last user message and the assistant's answer. Retrieval uses the last user message.

## Development

```bash
uv run ruff check . && uv run ruff format --check .   # PEP 8 / lint
uv run mypy src                                       # strict typing
uv run pytest                                         # tests (no DB or Ollama needed)
cd frontend && npm run typecheck && npm run build    # TypeScript strict
```
