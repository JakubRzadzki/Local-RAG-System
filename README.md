<div align="center">

# Local RAG System

**Chat with your own documents, 100% locally. Optionally add live web search.**

Upload TXT / Markdown / PDF files, pick any model installed in [Ollama](https://ollama.com), and get streamed answers together with the exact source chunks that were used.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![CI](https://github.com/JakubRzadzki/Local-RAG-System/actions/workflows/ci.yml/badge.svg)
![Typing](https://img.shields.io/badge/typing-mypy%20strict-blue)

[Overview](#overview) · [Tech stack](#tech-stack) · [Architecture](#architecture) · [How it works](#how-it-works) · [Quick start](#quick-start) · [Tested on](#tested-on) · [API](#api) · [Development](#development)

</div>

---

## Overview

A full-stack, ChatGPT-style application for asking questions about your own files. Everything runs on your machine: the embeddings, the vector search and the language model. The RAG (Retrieval-Augmented Generation) pipeline is written from scratch. **There is no LangChain and no LlamaIndex**, only Python, the official `ollama` client and PostgreSQL with `pgvector`.

Every answer shows which document, chunk, PDF page and similarity score each cited excerpt came from, so you can verify where a claim originates.

### Features

| Area | What you get |
|---|---|
| **Chat** | ChatGPT-style UI, token-by-token streaming, Markdown rendering, stop button |
| **Models** | Picker populated from your locally installed Ollama models (embedding-only models are filtered out) |
| **Tuning** | Per request: `temperature`, `top_k`. Per upload: `chunk_size`, `chunk_overlap` |
| **Sources** | Under every answer: filename, chunk index, PDF page, cosine similarity, chunk text |
| **Web search** | Optional **Web** toggle: the question is also searched on DuckDuckGo and the results are cited like document excerpts (off by default) |
| **Scoping** | Restrict a conversation to selected documents |
| **History** | Conversations are stored in PostgreSQL. Reopen, rename or delete them in the *Chats* tab. A partial answer is kept if you press stop |
| **Preview** | Inspect every stored chunk of a file, or jump from a cited source straight to its highlighted chunk |
| **Self-aware** | The assistant knows how the app works (built-in guide in `services/app_guide.py`), so you can ask *"How does this application work?"* |
| **Robust streaming** | Keep-alive pings while a large model loads, so the connection does not drop |
| **Docker** | One command runs database, backend and frontend |

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18, TypeScript (strict, no `any`), Vite, `react-markdown` | Typed, fast dev loop, small bundle (~88 kB gzipped) |
| Backend | Python 3.13, FastAPI, Pydantic v2, pydantic-settings | Async endpoints, request/response validation, typed settings |
| LLM runtime | [Ollama](https://ollama.com) via the official `ollama` async client | Local models, embeddings and chat through one API |
| Embeddings | `nomic-embed-text` (768 dimensions) with task prefixes | Small, fast, good retrieval quality |
| Vector store | PostgreSQL 17 + `pgvector`, HNSW index, cosine distance | One database for vectors, documents and chat history |
| DB driver | `psycopg` 3 with async connection pool | Native async, `pgvector` type support |
| PDF parsing | `pypdf` | Pure Python, page-level extraction |
| Web search | `ddgs` (DuckDuckGo) | No API key needed |
| Serving | nginx (static files + streaming-safe `/api` proxy), Docker Compose | Production-like local setup |
| Quality | `ruff` (PEP 8 + lint rules), `mypy --strict`, `pytest` (78 tests incl. pgvector integration), `tsc --strict` | Typed and tested end to end |

The codebase is about 4,000 lines of Python and TypeScript.

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        UI["React + TypeScript<br/>(Vite build served by nginx)"]
    end

    subgraph Docker["Docker Compose"]
        NG["nginx :8080<br/>static files + /api proxy"]
        subgraph API["FastAPI backend :8000"]
            direction TB
            R["routers<br/><i>HTTP only</i>"] --> S["services<br/><i>business logic</i>"] --> D["repositories<br/><i>data access</i>"]
        end
        PG[("PostgreSQL 17<br/>+ pgvector")]
    end

    OL["Ollama on the host<br/>chat + embeddings (GPU)"]
    WEB["DuckDuckGo<br/>(only if Web is on)"]

    UI -- "HTTP + NDJSON stream" --> NG --> R
    D --> PG
    D --> OL
    D -.-> WEB
```

The backend follows strict separation of concerns:

| Layer | Responsibility | Lives in |
|---|---|---|
| **Routers** | Routing and HTTP status codes only. No logic, no SQL | `routers/` |
| **Services** | Chunking, text extraction, ingestion, prompt building, RAG orchestration | `services/` |
| **Repositories** | All SQL/pgvector queries, the Ollama client and web search | `repositories/` |
| **Schemas** | Pydantic request/response DTOs | `schemas/` |

Dependencies are wired with FastAPI's dependency injection (`dependencies.py`), so each layer can be replaced by a fake in tests. The API tests do exactly that and need neither a database nor Ollama.

### Data model

```mermaid
erDiagram
    DOCUMENTS ||--o{ CHUNKS : "has"
    CONVERSATIONS ||--o{ MESSAGES : "has"

    DOCUMENTS {
        int id PK
        text filename
        text content_type
        int size_bytes
        int chunk_count
        int chunk_size
        int chunk_overlap
        timestamptz created_at
    }
    CHUNKS {
        int id PK
        int document_id FK
        int chunk_index
        int page
        text content
        vector768 embedding "HNSW cosine index"
    }
    CONVERSATIONS {
        int id PK
        text title
        text model
        timestamptz updated_at
    }
    MESSAGES {
        int id PK
        int conversation_id FK
        text role
        text content
        jsonb sources
    }
```

### Frontend structure

```mermaid
flowchart TB
    App --> Sidebar
    App --> TopBar["ModelSelect + SettingsPanel"]
    App --> ChatWindow
    App --> Composer["Composer (Web toggle)"]
    App --> PreviewModal
    Sidebar --> ConversationList
    Sidebar --> DocumentList
    Sidebar --> UploadZone
    ChatWindow --> MessageBubble --> SourceList

    App -.-> useChat
    App -.-> useModels
    App -.-> useDocuments
    App -.-> useConversations
    useChat & useModels & useDocuments & useConversations --> client["api/client.ts<br/>typed fetch + NDJSON reader"]
```

<details>
<summary><b>Project structure</b></summary>

```
src/local_rag_system/
├── config.py            settings (env vars prefixed RAG_)
├── database.py          async pool + schema
├── dependencies.py      dependency injection wiring
├── exceptions.py        domain errors -> HTTP status in main.py
├── main.py              app factory, CORS, error mapping
├── event_loop.py        SelectorEventLoop factory (psycopg async on Windows)
├── routers/             health, models, documents, conversations, chat
├── schemas/             Pydantic request/response DTOs and the chat event protocol
├── services/            chunking, text extraction, embedding, ingestion, conversations,
│                        prompt builder, app guide, RAG pipeline
└── repositories/        document, chunk, conversation, ollama, web search

frontend/src/
├── api/client.ts        typed fetch + NDJSON stream reader
├── hooks/               useChat, useModels, useDocuments, useConversations, useLocalStorage
└── components/          Sidebar, ConversationList, DocumentList, UploadZone, ModelSelect,
                         SettingsPanel, ChatWindow, MessageBubble, SourceList, Composer,
                         PreviewModal

sample_docs/             ready-to-use test documents (English; TXT, MD, PDF)
tests/                   pytest suite (78 tests); tests/integration needs Postgres
Dockerfile, docker-compose.yml, frontend/Dockerfile, frontend/nginx.conf
```

</details>

## How it works

### 1. Indexing (on upload)

```mermaid
flowchart LR
    A[Upload file] --> B["Extract text<br/>TXT / MD / PDF per page"]
    B --> C["Chunk<br/>paragraph-aware<br/>size + overlap"]
    C --> D["Embed in batches<br/>nomic-embed-text"]
    D --> E[("pgvector<br/>HNSW index")]
```

- **Chunking** keeps paragraphs together where possible and carries an overlap (trimmed to a word boundary) into the next chunk. Paragraphs longer than the chunk size are split by characters. PDFs are chunked page by page, so every chunk knows its page number.
- **Embedding** uses the `search_document:` prefix that `nomic-embed-text` was trained with. Embeddings are computed *before* anything is written, so a failed upload leaves nothing behind.

### 2. Answering (on question)

```mermaid
flowchart LR
    Q[Question] --> E["Embed query<br/>(search_query: prefix)"]
    E --> S[("Cosine top-k<br/>search")]
    W["Web search<br/>(optional)"]
    Q -.-> W
    S --> P["Build prompt:<br/>rules + app guide +<br/>numbered excerpts"]
    W -.-> P
    P --> L["Stream answer<br/>from chosen model"]
    L --> A["Answer with<br/>citations [1], [2], ..."]
    A --> H[("Save to<br/>chat history")]
```

The system prompt tells the model to:

- answer document questions from the numbered excerpts and cite them as `[1]`, `[2]`, and say so when the excerpts do not contain the answer,
- answer questions about the app itself from a built-in guide,
- answer general questions (definitions, simple facts, coding help) from its own knowledge without refusing,
- use web results for current facts and cite them with the same numbering.

### 3. Streaming protocol

The chat endpoint streams newline-delimited JSON, so the UI can show the sources first and then the text as it is generated.

```mermaid
sequenceDiagram
    participant C as Browser
    participant S as FastAPI
    participant O as Ollama
    C->>S: POST /api/chat
    S-->>C: conversation (id, title)
    S->>O: embed query
    S-->>C: sources (documents + web)
    S->>O: chat (stream)
    loop while the model is loading or thinking
        S-->>C: ping (every 10 s)
    end
    loop for each generated token
        O-->>S: token
        S-->>C: token
    end
    S-->>C: done
    Note over S: answer saved to the conversation
```

Design details worth knowing:

- Failures after streaming has started are reported in-band as an `error` event, because the HTTP status is already sent.
- If you press stop, the partial answer is still saved (the save is shielded from cancellation).
- `ping` events keep the connection alive while a large model is being loaded into memory. Without them, proxies and browsers may treat the silent connection as dead and show a *network error*.
- On Windows, psycopg's async mode cannot use the default `ProactorEventLoop`, so the app runs on a `SelectorEventLoop` (`event_loop.py`).

### 4. Web search and privacy

The **Web** toggle is off by default. When it is on, **only the text of your question** is sent to DuckDuckGo, and the top 5 results (title, URL, snippet) are added to the prompt as numbered sources with links. Your documents are never sent anywhere. If the search fails, the assistant is told so and answers without it.

> [!NOTE]
> Web results are search-result snippets, not full pages. That is enough for definitions and news headlines, but not for data that only lives inside a page, such as an hourly weather table. In that case the model will point you to the sources instead of inventing numbers.

### 5. Retrieval quality, reliability and security notes

- **Similarity threshold.** Chunks below the threshold are not given to the model. With `nomic-embed-text` on the sample documents, relevant questions had a best match of 0.74-0.84 and unrelated ones (*"What is photosynthesis?"*, *"hello how are you"*) at most 0.57, so the built-in value for that model is 0.6. Similarity scales differ between embedding models, so the built-in value only applies to models it was measured for; for any other model **no threshold is applied** (and a warning is logged at startup) until you set `RAG_MIN_SCORE` yourself.
- **Follow-up questions.** A short message after earlier turns (under 12 words, e.g. *"and which one is the largest?"*) is first rewritten by the chosen model into a standalone query using the recent conversation. The rewritten query is used for vector search and web search, while the prompt and the saved history keep your original wording. If the rewrite fails, the original text is used. On the sample documents, the raw follow-up matched one chunk with similarity 0.67, and the rewritten query matched two with 0.79 and 0.70. The cost is one extra short model call for follow-ups only.
- **Filtered search is exact.** When a conversation is limited to selected documents, those documents' chunks are selected first and ranked exactly. A plain HNSW query applies the `WHERE` only after it has produced its candidates, and an integration test showed that this can return **zero** results for a small document next to a large one.
- **Chunking.** Handles Windows (`\r\n`) and single-newline text (typical for PDFs), cuts on word boundaries and never exceeds `chunk_size`.
- **Atomic, idempotent ingestion.** A document and its chunks are written in one transaction, and the SHA-256 of the extracted text is unique, so uploading the same document twice returns `409` instead of duplicating chunks, even if the line endings differ. PDFs that need a password to open, and damaged PDFs, return `422`; PDFs that only restrict printing or copying (owner password) are read normally. The size limit is enforced without loading the whole file.
- **Prompt-injection hygiene.** Document excerpts and web results are untrusted. They are placed in tagged `<documents>` / `<web_results>` blocks in the user message, never in the `system` prompt, closing tags inside them are neutralised, and the system prompt tells the model not to follow instructions found there. This reduces the risk but cannot eliminate it.
- **Network exposure.** The app has no authentication, so Docker publishes the web UI and the database only on `127.0.0.1`. Change the port mappings in `docker-compose.yml` only if you add authentication. The backend container runs as an unprivileged user and has a healthcheck; the frontend container starts only after it is healthy.

## Quick start

### Requirements

- [Ollama](https://ollama.com) running on the host, with an embedding model and at least one chat model
- Docker (for the one-command setup), or Python 3.13 + [uv](https://docs.astral.sh/uv/) + Node.js 20+ for local development

```bash
ollama pull nomic-embed-text   # required: embeddings (768 dimensions)
ollama pull gemma3:4b          # any chat model works; this is just an example
```

Any installed model with the `completion` capability shows up in the model picker.

### Option A: Docker (everything in containers)

```bash
docker compose up -d --build
```

Open **http://localhost:8080**. This starts PostgreSQL + pgvector, the FastAPI backend and an nginx container serving the frontend. Ollama stays on the host so it can use your GPU; the backend reaches it through `host.docker.internal`.

```bash
docker compose logs -f backend   # logs
docker compose down              # stop (add -v to also delete the database)
```

### Option B: local development

```bash
# 1. database only
docker compose up -d db

# 2. backend (http://127.0.0.1:8000, interactive docs at /docs)
uv sync
uv run local-rag-system

# 3. frontend (http://localhost:5173, proxies /api to the backend)
cd frontend
npm install
npm run dev
```

> [!NOTE]
> **Windows:** use `127.0.0.1` rather than `localhost` for the database (the defaults already do): `localhost` may resolve to IPv6 first, where Docker does not listen, which makes connections hang. `uv run local-rag-system` configures the required `SelectorEventLoop` for you. If you start uvicorn manually, add `--loop local_rag_system.event_loop:selector_loop_factory`.

### Try it

Drag the files from `sample_docs/` into the *Documents* tab, then ask:

- *How many vacation days does a NovaTech employee get?*
- *Which planet has the strongest winds?*
- *Which command runs tests until the first failure?*
- *How does this application work?*
- Switch **Web** on and ask about something recent.

> [!IMPORTANT]
> If you change the embedding model, set `RAG_EMBEDDING_MODEL` and `RAG_EMBEDDING_DIM` and recreate the `chunks` table. The vector size is fixed per column.

### Configuration

Environment variables (or a `.env` file), all optional:

| Variable | Default |
|---|---|
| `RAG_DATABASE_URL` | `postgresql://postgres:postgres@127.0.0.1:5432/rag` |
| `RAG_OLLAMA_HOST` | `http://localhost:11434` |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` |
| `RAG_EMBEDDING_DIM` | `768` |
| `RAG_MIN_SCORE` | unset: `0.6` for `nomic-embed-text`, no threshold for other models. Minimum cosine similarity for a chunk to be used |
| `RAG_DEFAULT_CHUNK_SIZE` | `800` |
| `RAG_DEFAULT_CHUNK_OVERLAP` | `100` |
| `RAG_MAX_UPLOAD_BYTES` | `20971520` (20 MB) |
| `RAG_CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` |

## Tested on

All numbers below were measured on the development machine during this project. They are indicative of this hardware and these models, not a formal benchmark.

| | |
|---|---|
| **GPU** | NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12 GB VRAM |
| **OS** | Windows 11 Home |
| **Runtime** | Ollama 0.32 (host), Docker Desktop for the database/backend/frontend containers |
| **Models** | `gemma4:12b`, `gemma4:26b`, `qwen2.5-coder:14b` (chat), `nomic-embed-text` (embeddings) |

**Generation speed** (single request, model already loaded, 200 tokens):

| Model | Size on disk | Tokens / second | Notes |
|---|---|---|---|
| `gemma4:12b` | 7.6 GB | 21.6 | fits in 12 GB VRAM |
| `gemma4:26b` | 18 GB | 31.8 | larger than VRAM, still the fastest in this test |
| `qwen2.5-coder:14b` | 9.0 GB | 16.3 | 10.5 of 15.7 GB resident in VRAM when loaded |

**RAG latency** through the full stack (nginx -> backend -> pgvector -> Ollama), warm model, one question over the sample documents:

| Model | Sources shown after | First token after | Whole answer |
|---|---|---|---|
| `gemma4:12b` | ~2.2 s | ~2.7 s | ~5.1 s (50 tokens) |
| `gemma4:26b` | ~2.3 s | ~3.1 s | ~5.4 s (40 tokens) |

**Indexing** the four sample documents (TXT, MD, PDF, TXT) took between 0.2 and 0.8 s each, including extraction, chunking, embedding and storage. Embedding a batch of 32 chunks of about 150 tokens took roughly 1.5 s on the first call.

What to expect:

- The **first request after switching models** can take one to two minutes while Ollama loads the model into memory (the 26B model took about two minutes cold). The keep-alive pings exist for this reason.
- Retrieval over this small corpus is fast; the model dominates the latency.

Not tested: Linux and macOS, other GPUs, CPU-only inference, large corpora (thousands of documents) and concurrent users.

## What was achieved

- A complete RAG pipeline without any RAG framework: extraction, chunking, embedding, HNSW vector search, prompt construction and streamed generation.
- Strict layering (routers -> services -> repositories) that makes the logic testable without a database or an LLM.
- A usable chat product around it: model switching, parameter tuning, saved history, document preview, source inspection and optional web search.
- Verified citations: the answer to *"How many vacation days does a NovaTech employee get?"* cites the exact handbook chunk, which you can open from the answer.
- Full typing (`mypy --strict`, TypeScript `strict` with no `any`), PEP 8 enforced by `ruff`, and 78 automated tests, including integration tests against a real pgvector database.
- A reproducible one-command deployment with Docker Compose, with nginx configured so the token stream is not buffered.

### Known limitations

- Single-user: there is no authentication.
- Scanned PDFs are not supported (there is no OCR); they are rejected with a clear error.
- Follow-up rewriting depends on the chat model and only applies to short messages; a long follow-up that still relies on earlier turns is searched as written.
- Web results are snippets, not full pages (see above).
- Large models that do not fit in VRAM are slow to load.

## API

Interactive docs: `http://127.0.0.1:8000/docs` (local development).

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
| `409` | The same file (identical content) was already uploaded |
| `413` | File too large |
| `415` | Unsupported file type |
| `422` | No extractable text, damaged or password-protected PDF, or invalid chunking parameters |
| `503` | Ollama is not reachable |

### `POST /api/chat`

Request:

```json
{
  "model": "gemma3:4b",
  "messages": [{ "role": "user", "content": "What is top_k?" }],
  "options": { "temperature": 0.2, "top_k": 4, "document_ids": null, "web_search": false },
  "conversation_id": null
}
```

The response is `application/x-ndjson`, one JSON event per line:

```jsonl
{"type":"conversation","id":1,"title":"What is top_k?"}
{"type":"sources","sources":[{"index":1,"kind":"document","document_id":3,"filename":"rag-explained.md","chunk_index":2,"page":null,"url":null,"score":0.83,"content":"..."}]}
{"type":"ping"}
{"type":"token","content":"top"}
{"type":"token","content":"_k"}
{"type":"done"}
```

- The first event announces the conversation (new when `conversation_id` is `null`).
- Sources have `kind: "document"` or `kind: "web"`. Web sources carry a `url` and no chunk/score. Numbers are continuous, so documents come first and web results follow.
- The client sends the message history. The server stores the last user message and the assistant's answer.
- Retrieval uses the last user message, rewritten into a standalone query first if it is a short follow-up.
- `ping` can be ignored by clients; `error` ends the stream.

## Development

```bash
uv run ruff check . && uv run ruff format --check .   # PEP 8 / lint
uv run mypy src                                       # strict typing
uv run pytest                                         # 78 tests; the pgvector ones are skipped without Postgres
cd frontend && npm run typecheck && npm run build     # TypeScript strict
```

CI (`.github/workflows/ci.yml`) runs lint, `mypy`, the full test suite against a real `pgvector` service, and the frontend typecheck and build.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) and are kept small and atomic.
