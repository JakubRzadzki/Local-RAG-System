# Retrieval-Augmented Generation (RAG) explained

Retrieval-Augmented Generation combines a search step with a language model.
Instead of relying only on what the model memorised during training, the system
first **retrieves** relevant passages from a private knowledge base and then asks
the model to **generate** an answer grounded in those passages.

## The pipeline

1. **Ingestion** - documents are split into chunks of a few hundred characters.
   Neighbouring chunks overlap slightly so a sentence cut at a boundary is still
   understood in context.
2. **Embedding** - every chunk is converted into a vector (for example 768 numbers
   for `nomic-embed-text`). Texts with similar meaning end up close together.
3. **Indexing** - vectors are stored in a vector database. This project uses
   PostgreSQL with the `pgvector` extension and an HNSW index for fast approximate
   nearest-neighbour search.
4. **Retrieval** - the user's question is embedded with the same model and the
   `top_k` most similar chunks are fetched using cosine distance.
5. **Generation** - the chunks are placed in the prompt as numbered context and the
   language model writes an answer, citing the excerpts it used.

## Key parameters

| Parameter     | Effect                                                                 |
|---------------|------------------------------------------------------------------------|
| `chunk_size`  | Larger chunks keep more context but dilute the embedding's focus.      |
| `top_k`       | More retrieved chunks improve recall but add noise and prompt length.  |
| `temperature` | Low values (0.0-0.3) give factual answers; high values add creativity. |

## Why RAG instead of fine-tuning?

RAG needs no training run, the knowledge can be updated by simply uploading a new
file, and every answer can point back to its source. Fine-tuning is better for
teaching a model a *style* or a *skill* than for teaching it *facts*.

## Common failure modes

- **Hallucination** when the retrieved context does not contain the answer. A good
  prompt tells the model to admit that it does not know.
- **Poor chunking** that splits a table or a list in half.
- **Embedding mismatch** when queries and documents are embedded with different
  models, which makes the vectors incomparable.
