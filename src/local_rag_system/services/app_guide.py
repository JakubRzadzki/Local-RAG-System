"""Built-in description of the application, so the assistant can explain itself."""

APP_GUIDE = """\
About this application (use it when the user asks how the app works, what it can do, \
or how to use it):
- "Local RAG" is a ChatGPT-style app that answers questions about the user's own \
documents. Everything runs locally: embeddings, vector search and the language model \
(via Ollama); no data leaves the machine.
- Documents: the sidebar tab "Documents" uploads TXT, Markdown and PDF files (button or \
drag & drop). Each file is split into chunks, embedded with the embedding model \
(nomic-embed-text) and stored in PostgreSQL with pgvector. The eye icon opens a preview \
of the stored chunks. The checkboxes limit answers to the selected documents; with none \
selected, all documents are searched. The cross deletes a document.
- Chunking: "Chunking" under the upload button sets chunk size (characters per chunk) \
and overlap (characters shared by neighbouring chunks). It applies to files uploaded \
afterwards. Smaller chunks give more precise matches, larger ones keep more context.
- Asking questions: the question is embedded, the top-k most similar chunks are \
retrieved by cosine similarity, and they are passed to the chosen model as numbered \
context. The answer streams in and cites the excerpts as [1], [2]. The "sources" \
section under each answer shows the document, chunk number, PDF page, similarity \
score and text; "View in document" opens it in the preview.
- Model and parameters: the dropdown in the top bar lists the chat models installed in \
Ollama. "Parameters" sets temperature (0 = factual, 2 = creative) and top-k (how many \
chunks are retrieved).
- Web search: the "Web" toggle next to the message box lets the assistant also search \
the internet (DuckDuckGo) for current information such as news or weather. Web results \
appear as numbered sources with links and are cited like document excerpts. It is off \
by default; when on, the question text is sent to DuckDuckGo. Documents are never sent.
- Chats: every conversation is saved automatically. The sidebar tab "Chats" lists \
previous conversations; click one to continue it, use the pencil to rename it or the \
cross to delete it. "New chat" starts a fresh conversation. The stop button interrupts \
a streaming answer.
- Technology: FastAPI backend (routers -> services -> repositories), React + \
TypeScript frontend, PostgreSQL + pgvector, Ollama. No LangChain or LlamaIndex.\
"""
