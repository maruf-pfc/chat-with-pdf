# Low-level sequence (PDF ingestion)

```mermaid
sequenceDiagram
    Client->>Worker: POST /process-pdf (file)
    Worker->>Worker: Read bytes → Extract text
    Worker->>Worker: chunk_text(...)
    Worker->>EmbeddingModel: Create embedding(chunk1)
    EmbeddingModel-->>Worker: vector1

    Worker->>Postgres: INSERT document (filename, total_chunks)
    Postgres-->>Worker: document_id

    Worker->>Postgres: INSERT chunk1 (document_id, chunk_index, chunk_text, embedding)

    Worker->>EmbeddingModel: Create embedding(chunk2)
    Note over Worker: ...repeat for all chunks...

    Worker-->>Client: 200 { document_id, chunks }
```

## Low-Level Architecture

```txt
User Query
   │
   ▼
NestJS API
   │ 1. Validate query
   │ 2. Send query → worker (/search)
   ▼
Python Worker
   │ 1. Embed query locally
   │ 2. Vector similarity search (cosine)
   │ 3. Return top chunks
   ▼
NestJS API
   │ 3. Format chunks
   │ 4. Call Groq LLM to generate answer
   ▼
LLM Answer
   │
   ▼
UI (Final Response)
```
