# 1. HIGH-LEVEL SYSTEM EXPLANATION

Your system performs **three major operations**:

## A. Process & Store PDF

1. Upload PDF
2. Extract text
3. Split into chunks
4. Generate embedding for each chunk
5. Store chunks + embedding inside PostgreSQL (pgvector)

### B. Embedding-based Semantic Search

1. User gives query text
2. Convert query → embedding
3. Run pgvector similarity search
4. Return top-K most relevant chunks

### C. Core Technologies Used

| Component                 | Purpose                           |
| ------------------------- | --------------------------------- |
| **FastAPI**               | Web API framework                 |
| **pypdf**                 | Extract PDF text                  |
| **SentenceTransformer**   | Generate embeddings               |
| **PostgreSQL + pgvector** | Store vectors + similarity search |
| **psycopg2**              | DB connection                     |
| **dotenv**                | Load env variables                |

### 2. FLOW DIAGRAM (What you saw above)

The diagram visually represents:

```txt
Client → Upload PDF → FastAPI → Extract Text → Chunk Text → Generate Embeddings →
Store Into PostgreSQL → Vector Search
```

This shows the complete end-to-end pipeline.

## 3. DETAILED EXPLANATION OF THE CODE (Line-by-Line Understanding)

### A. Imports & Setup

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
```

You import all required libraries:

- FastAPI → API framework
- PdfReader → Read PDF
- psycopg2 → Database
- SentenceTransformer → Embeddings
- dotenv → Load .env variables
- pydantic → Validate request body

## B. Load environment variables

```python
load_dotenv()
```

Loads `.env` so the DB credentials become available.

## **C. Initialize FastAPI**

```python
app = FastAPI()
```

This creates the API application.

## 1. DATABASE CONNECTION

```python
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", 5433)
    )
```

This function returns a new DB connection using credentials from `.env`.
Default fallback: localhost + postgres.

## 2. LOAD EMBEDDING MODEL

```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

Loads a **local embedding model**.
This converts text → 384-dimension vector.

## 3. PDF TEXT EXTRACTION

```python
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    if not text.strip():
        raise ValueError("Empty PDF")

    return text
```

### Steps

1. Load PDF
2. Loop over pages
3. Extract text per page
4. Append
5. Error if PDF text is empty

## 4. CHUNKING THE TEXT

```python
def chunk_text(text, max_words=300):
    words = text.split()
    chunks, current = [], []

    for w in words:
        current.append(w)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks
```

### Explanation

- Splits PDF into **300-word blocks**.
- Each block becomes one database record.
- Helps with embedding efficiency and faster vector search.

## 5. GENERATE EMBEDDINGS

```python
def generate_embedding(text):
    emb = model.encode(text)
    return emb.tolist()
```

Converts chunk text → vector (Python list)
pgvector stores this list into a `vector` column.

## 6. PDF PROCESSING API

### POST /process-pdf

```python
@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
```

### Workflow inside:

### **1. Validate PDF**

```python
if not file.filename.endswith(".pdf"):
    raise HTTPException(400, "File must be a PDF")
```

### **2. Extract text**

```python
text = extract_pdf_text(file.file)
```

### **3. Chunk it**

```python
chunks = chunk_text(text)
```

### **4. Insert document metadata**

```python
cur.execute(
    "INSERT INTO documents (filename, total_chunks) VALUES (%s, %s) RETURNING id",
    (file.filename, len(chunks))
)
doc_id = cur.fetchone()[0]
```

Database table:

```txt
documents:
- id
- filename
- total_chunks
```

### **5. Insert each chunk with embeddings**

```python
for idx, chunk in enumerate(chunks):
    emb = generate_embedding(chunk)
    cur.execute(
        """
        INSERT INTO chunks (document_id, chunk_index, chunk_text, embedding)
        VALUES (%s, %s, %s, %s)
        """,
        (doc_id, idx, chunk, emb)
    )
```

Each record includes:

- document_id (FK)
- chunk index (0,1,2…)
- chunk text
- embedding (vector)

### 6. Return response

```python
return {
    "message": "PDF processed successfully",
    "document_id": doc_id,
    "total_chunks": len(chunks)
}
```

## 7. VECTOR SEARCH ENDPOINT

```python
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
```

This validates incoming JSON.

## **POST /search**

```python
embedding = model.encode(query).tolist()
```

Convert user query → vector.

## **Run pgvector similarity**

```sql
SELECT chunk_text, 1 - (embedding <=> %s::vector) AS score
FROM chunks
ORDER BY embedding <=> %s::vector
LIMIT %s;
```

### Explanation

`<=>` is pgvector’s **cosine distance operator**.

- Lower distance = more similar
- To convert distance → similarity: `1 - distance`

## **Return top results**

```python
{
    "text": r[0],
    "score": float(r[1])
}
```

## 🎉 **FINAL RESULT: WHAT THIS SYSTEM DOES**

This backend enables:

### ✔ Upload PDF

→ Extract text
→ Split text
→ Embed each chunk
→ Store in pgvector

### ✔ Semantic Search

→ Query text
→ Convert to embedding
→ Compare with chunk embeddings
→ Return best matches

This is **exactly like ChatGPT Retrieval**, but self-hosted.

## 1) What `main.py` does — component & flow (high-level)

**Purpose:** Accept a PDF, extract text, split into smaller chunks, produce embeddings for each chunk, and store the chunks and embeddings in Postgres (pgvector). This prepares data for semantic search / RAG.

Flow summary:

1. Receive PDF file (HTTP POST `/process-pdf`).
2. Validate filename.
3. Read bytes → extract text from PDF pages.
4. Chunk text into smaller passages.
5. For each chunk:

   - create embedding (local model or remote API)
   - insert chunk metadata + embedding into `chunks` table

6. Insert / update `documents` table with metadata (filename, total_chunks).
7. Return success + IDs.

Key tables:

- `documents(id, filename, total_chunks, created_at)`
- `chunks(id, document_id, chunk_index, chunk_text, embedding VECTOR(D))`

## 2) File walkthrough — function by function (explicit)

(You can match these to your file; names may differ.)

### `get_db()`

- Creates a new `psycopg2` connection using env vars (`DB_HOST/DB_PORT/DB_USER/DB_PASS/DB_NAME`).
- Important: in Docker compose, `DB_HOST` often equals the service name `db`.

**Notes:** Prefer connection pooling (e.g., `psycopg2.pool.SimpleConnectionPool`) when load increases.

### `client = Groq(api_key=...)` _(or local SentenceTransformer model)_

- When remote (Groq): `client.embeddings.create(model=..., input=...)`
- When local (SentenceTransformer): `model.encode(text)` (returns numpy array)

**Notes:** Choose either remote or local based on latency/compute/cost.

---

### `extract_pdf_text(file_bytes_or_filelike)`

- If you get raw bytes, wrap with `io.BytesIO(file_bytes)` and call `PdfReader(...)`.
- Iterate pages and concatenate `page.extract_text()` results.
- Edge cases: scanned PDFs (no text) — you'd need OCR (Tesseract/paddleocr).

---

### `chunk_text(text, max_words=300)`

- Splits text by whitespace; groups into chunks of `max_words` tokens (or words).
- Optionally use _tokenizer-based_ chunking (count tokens, not words) for LLM prompt size planning.
- Consider overlap (e.g., 20–50 words) to preserve context at chunk boundaries.

---

### `generate_embedding(text)`

- If using Groq:

  - call `client.embeddings.create(model="nomic-embed-text", input=text)` (make sure model name you have access to is correct).

- If using local:

  - `emb = model.encode(text)` then `.tolist()` or `list(emb)` for psycopg2 insertion.

- Return vector (list/array) with dimension D.

---

### `/process-pdf` endpoint

- Validate `.pdf`.
- Read file bytes: `file_bytes = await file.read()`.
- `text = extract_pdf_text(file_bytes)` → `chunks = chunk_text(text)`.
- Insert `documents` row: `INSERT INTO documents (filename, total_chunks) VALUES (...) RETURNING id`.
- For each chunk:

  - `embedding = generate_embedding(chunk)`
  - `INSERT INTO chunks (document_id, chunk_index, chunk_text, embedding) VALUES (...)`

- Commit.

**Important error handling** (must be present):

- DB connection failures → return 500 with clear message.
- Embedding model 404/permission error → catch and return helpful message.
- If insertion fails midway, either use transactions or rollback to avoid partial data.

## 3) Theory — embeddings, vector DB, indexing, search

### What are embeddings?

- An **embedding** is a numerical vector (list of floats) that represents semantic meaning of text.
- Similar texts map to nearby vectors in high-dimensional space.
- Models (sentence-transformers, OpenAI, Groq, etc.) map variable-length text → fixed-length vectors (D dims).

### Embedding dimension (D)

- Different models produce different dimensions: e.g. 384, 512, 768, 1536, etc.
- The `vector(D)` column type in pgvector must match the embedding length exactly.
- Mismatched dimension → insertion errors.

### Similarity metrics

- **Cosine similarity** (or cosine distance) is most common for semantic search.
- pgvector supports `<->` operator (distance) and `vector_cosine_ops` for cosine search with ivfflat.

### Vector Indexes (IVFFLAT)

- `USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)` speeds up similarity search for large collections.
- IVFFlat trades approximate search speed vs exactness. You can tune `lists` and search probes.
- Before altering vector column dimension, you must drop dependent indexes, change type, and recreate index.

### Chunking & overlap

- Chunk size: tradeoff between context and number of chunks. Aim for ~200–500 tokens per chunk depending on LLM prompt limit.
- Overlap: overlapping windows keeps context near boundaries (common practice: 10–30% overlap).

### RAG (Retrieval-Augmented Generation) pipeline outline

1. User query → compute embedding.
2. Search vector DB for nearest chunks (SQL example below).
3. Combine top-K chunks into a context (possibly with filters, recency).
4. Build prompt: system + context + question.
5. Call LLM to generate final answer (or use instruction-tuned model).
6. Optionally save conversation or provenance.

SQL similarity example:

```sql
SELECT id, chunk_text, embedding <#> $1 as distance
FROM chunks
ORDER BY embedding <-> $1
LIMIT 5;
```

or (for cosine)

```sql
SELECT chunk_text
FROM chunks
ORDER BY embedding <-> $1
LIMIT 5;
```

`$1` is the parameter vector passed from your driver.

---

## 4) Architecture diagrams

### High-level architecture [Click here](./high-level.md)

### Low-level sequence (PDF ingestion) [Click Here](./low-level.md)
