from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

# ----------------------------
# DB connection
# ----------------------------
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", 5433)
    )

# ----------------------------
# Local embedding model
# ----------------------------
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ----------------------------
# PDF → Text
# ----------------------------
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    if not text.strip():
        raise ValueError("Empty PDF")

    return text


# ----------------------------
# Chunking logic
# ----------------------------
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


# ----------------------------
# Generate Embedding (local)
# ----------------------------
def generate_embedding(text):
    emb = model.encode(text)
    return emb.tolist()


# ----------------------------
# Upload PDF API
# ----------------------------
@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    text = extract_pdf_text(file.file)
    chunks = chunk_text(text)

    conn = get_db()
    cur = conn.cursor()

    # Save doc record
    cur.execute(
        "INSERT INTO documents (filename, total_chunks) VALUES (%s, %s) RETURNING id",
        (file.filename, len(chunks))
    )
    doc_id = cur.fetchone()[0]

    # Insert chunks
    for idx, chunk in enumerate(chunks):
        emb = generate_embedding(chunk)
        cur.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, chunk_text, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (doc_id, idx, chunk, emb)
        )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "PDF processed successfully",
        "document_id": doc_id,
        "total_chunks": len(chunks)
    }

# --------------------------------
# VECTOR SEARCH ENDPOINT
# --------------------------------
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
async def search(body: SearchRequest):
    query = body.query
    top_k = body.top_k

    embedding = model.encode(query).tolist()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT chunk_text, 1 - (embedding <=> %s::vector) AS score
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (embedding, embedding, top_k)
    )

    rows = cur.fetchall()
    conn.close()

    return {
        "query": query,
        "results": [
            {"text": r[0], "score": float(r[1])}
            for r in rows
        ]
    }

