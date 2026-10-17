<div align="center">

# Local RAG System

**Chat with your own documents, 100% locally.**

Upload TXT / Markdown / PDF files, pick any model installed in [Ollama](https://ollama.com), and get streamed answers together with the exact source chunks that were used.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000)
![Typing](https://img.shields.io/badge/typing-mypy%20strict-blue)

[Features](#features) · [Architecture](#architecture) · [Requirements](#requirements) · [Running](#running) · [Configuration](#configuration) · [API](#api) · [Development](#development)

</div>

---

The RAG pipeline is written from scratch: **no LangChain, no LlamaIndex**. Just Python, the official `ollama` client and PostgreSQL with `pgvector`.

Each answer comes with the document, chunk number, PDF page and similarity score of every chunk the model saw, so you can verify where a claim comes from.

## Features

| Area | What you get |
|---|---|
| **Chat** | ChatGPT-style UI, token-by-token streaming, Markdown rendering |
| **Models** | Picker populated from your locally installed Ollama models (embedding-only models are filtered out) |
| **Tuning** | Per request: `temperature`, `top_k`. Per upload: `chunk_size`, `chunk_overlap` |
| **Sources** | Under every answer: filename, chunk index, PDF page, cosine similarity, chunk text |
| **Scoping** | Restrict a conversation to selected documents |
| **History** | Conversations stored in PostgreSQL. Reopen, rename or delete them in the *Chats* tab. Partial answers are kept when you press stop |
| **Preview** | Inspect every stored chunk of a file and jump from a cited source straight to its highlighted chunk |
| **Self-aware** | The assistant knows how the app works (built-in guide in `services/app_guide.py`), so you can ask *"How does this application work?"* |
| **Chunking** | Paragraph-aware with overlap, per-page for PDFs |
| **Typing** | Pydantic on the backend, strict TypeScript (no `any`) on the frontend |

## Architecture

```mermaid
flowchart LR
    UI["React + TypeScript<br/>(Vite)"] -- "HTTP / NDJSON" --> API

    subgraph API ["FastAPI"]
        direction TB
        R["routers<br/><i>HTTP only</i>"] --> S["services<br/><i>business logic</i>"] --> D["repositories<br/><i>data access</i>"]
    end

    D --> PG[("PostgreSQL<br/>+ pgvector")]
    D --> OL["Ollama<br/>embeddings + chat"]
```

| Layer | Responsibility |
|---|---|
| `routers/` | Routing and status codes only |
| `services/` | Chunking, extraction, ingestion, prompt building, RAG orchestration |
| `repositories/` | pgvector (documents, chunks) and the Ollama client |

### RAG flow

**Indexing (on upload)**

```mermaid
flowchart LR
    A[Upload file] --> B[Extract text]
    B --> C[Chunk<br/>size + overlap]
    C --> D["Embed<br/>nomic-embed-text"]
    D --> E[("pgvector<br/>HNSW index")]
```

**Answering (on question)**

```mermaid
flowchart LR
    Q[Question] --> E["Embed query"]
    E --> S[("Cosine top-k<br/>search")]
    S --> P["Build prompt<br/>with numbered context"]
    P --> L["Stream answer<br/>from chosen model"]
    L --> A["Answer with<br/>citations [1], [2], ..."]
```

The model is instructed to cite excerpts as `[1]`, `[2]`, and so on, and to say so when the context does not contain the answer.

<details>
<summary><b>Project structure</b></summary>

```
src/local_rag_system/
├── config.py            settings (env vars prefixed RAG_)
├── database.py          async pool + schema
├── dependencies.py      dependency injection wiring
├── exceptions.py        domain errors -> HTTP status in main.py
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

sample_docs/             ready-to-use test documents (English; TXT, MD, PDF)
tests/                   pytest suite
```

</details>

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

> [!IMPORTANT]
> If you change the embedding model, set `RAG_EMBEDDING_MODEL` and `RAG_EMBEDDING_DIM` and recreate the `chunks` table. The vector size is fixed per column.

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

- *How many vacation days does a NovaTech employee get?*
- *Which planet has the strongest winds?*
- *Which command runs tests until the first failure?*

> [!NOTE]
> **Windows:** psycopg's async mode needs a `SelectorEventLoop`. `uv run local-rag-system` configures this for you. If you start uvicorn manually, add `--loop local_rag_system.event_loop:selector_loop_factory`.

## Configuration

Environment variables (or a `.env` file), all optional:

| Variable | Default |
|---|---|
| `RAG_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/rag` |
| `RAG_OLLAMA_HOST` | `http://localhost:11434` |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` |
| `RAG_EMBEDDING_DIM` | `768` |
| `RAG_DEFAULT_CHUNK_SIZE` | `800` |
| `RAG_DEFAULT_CHUNK_OVERLAP` | `100` |
| `RAG_MAX_UPLOAD_BYTES` | `20971520` (20 MB) |
| `RAG_CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` |

## API

Interactive docs: `http://127.0.0.1:8000/docs`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/models` | Installed Ollama models with `capabilities` and `supports_chat`. Also reports whether the embedding model is installed |
| `GET` | `/api/documents` | List indexed documents |
| `POST` | `/api/documents` | Multipart upload: `file` (TXT/MD/PDF), optional `chunk_size` (100-4000), `chunk_overlap` (0-1000). Returns `201` |
| `GET` | `/api/documents/{id}/preview` | Document metadata plus all its chunks (`chunk_index`, `page`, `content`) in reading order |
| `DELETE` | `/api/documents/{id}` | Delete a document and its chunks (`204`, or `404`) |
| `GET` | `/api/conversations` | Saved conversations, most recently active first |
| `GET` | `/api/conversations/{id}` | A conversation with its messages and their sources |
| `PATCH` | `/api/conversations/{id}` | Rename: `{"title": "..."}` |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation (`204`, or `404`) |
| `POST` | `/api/chat` | Streaming RAG answer (see below) |

**Upload errors**

| Status | Meaning |
|---|---|
| `413` | File too large |
| `415` | Unsupported file type |
| `422` | No extractable text, or invalid chunking parameters |
| `503` | Ollama is not reachable |

### `POST /api/chat`

Request:

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
{"type":"sources","sources":[{"index":1,"document_id":3,"filename":"rag-explained.md","chunk_index":2,"page":null,"score":0.83,"content":"..."}]}
{"type":"token","content":"top"}
{"type":"token","content":"_k"}
{"type":"done"}
```

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    C->>S: POST /api/chat
    S-->>C: conversation (id, title)
    S-->>C: sources (retrieved chunks)
    loop for each generated token
        S-->>C: token
    end
    S-->>C: done
```

- The first event announces the conversation (new when `conversation_id` is `null`).
- The client sends the message history. The server stores the last user message and the assistant's answer.
- Retrieval uses the last user message.
- Failures after streaming has started are reported in-band as `{"type":"error","message":"..."}`.

## Development

```bash
uv run ruff check . && uv run ruff format --check .   # PEP 8 / lint
uv run mypy src                                       # strict typing
uv run pytest                                         # tests (no DB or Ollama needed)
cd frontend && npm run typecheck && npm run build     # TypeScript strict
```
