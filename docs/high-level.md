# High-level architecture (text/ASCII)

```mermaid
+----------------+         +----------------+        +----------------+
|   Next.js UI   | <--->   |  NestJS API    | <----> |  Postgres +    |
| (client)       |         | (ai-text-intel)|        |  pgvector      |
| routes: /ask   |         | routes: /ai,   |        |  (documents,   |
| /upload, /tools|         | /pdf/query     |        |   chunks)      |
+----------------+         +----------------+        +----------------+
                                      ^
                                      |
                           +----------------------+
                           | Worker Service (FastAPI) |
                           | - /process-pdf           |
                           | - extracts, chunks, embeds|
                           | - inserts into pgvector   |
                           +--------------------------+
                           ^             ^
                           |             |
                   +--------------+  +----------------+
                   | Groq API or  |  |  Local model   |
                   | other LLMs   |  | SentenceTransformers |
                   +--------------+  +----------------+
```

## High-Level Architecture

```mermaid

                ┌───────────────────────────┐
                │         NEXT.js UI        │
                └───────────┬───────────────┘
                            │ HTTP
                            ▼
                ┌───────────────────────────┐
                │       NestJS API          │
                │  /ask, /upload, /docs     │
                └───────────┬───────────────┘
                            │ REST call
                            ▼
                ┌───────────────────────────┐
                │       Python Worker       │
                │   /process-pdf, /search   │
                └───────────┬───────────────┘
                            │ SQL
                            ▼
                ┌───────────────────────────┐
                │     PostgreSQL + Vector   │
                └───────────────────────────┘
```
