"""
PDF → Text → Chunk → Embedding → pgvector
RAG Search + Conversation Memory Worker
---------------------------------------

This FastAPI worker handles:
1. PDF extraction
2. Chunking
3. Embedding generation (Sentence Transformers)
4. Storing chunks & embeddings into pgvector
5. Semantic search over the embeddings
6. Conversation memory storage (messages table)
7. RAG prompt building for NestJS LLM

NestJS will call:
- /process-pdf  → when user uploads PDFs
- /ask          → when user asks a question
- /search       → internal simple search

LLM completion happens in NestJS.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from pydantic import BaseModel
from typing import List, Optional

import os
import psycopg2
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load .env
load_dotenv()

app = FastAPI(title="PDF Worker Service")


# ============================================================================
# DATABASE CONNECTION
# ============================================================================
def get_db():
    """
    Helper function to connect to PostgreSQL.
    Uses pgvector + standard tables:
      - documents
      - chunks
      - messages
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", 5433)
    )


# ============================================================================
# EMBEDDING MODEL (Sentence Transformers)
# ============================================================================
"""
We use a LOCAL embedding model to avoid API costs:
Model size: 384-dim vector
Fast and ideal for PDF RAG indexing.
"""
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# ============================================================================
# PDF → TEXT EXTRACTION
# ============================================================================
def extract_pdf_text(pdf_file):
    """Extract raw text from a PDF using PyPDF."""
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"

    if not text.strip():
        raise ValueError("PDF text extraction failed (empty text).")

    return text


# ============================================================================
# TEXT CHUNKING
# ============================================================================
def chunk_text(text: str, max_words: int = 300):
    """
    Break PDF text into fixed-length chunks.
    Purpose:
    - PDF pages are too large for direct embedding
    - Chunking improves semantic search accuracy
    """
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


# ============================================================================
# EMBEDDING GENERATION (LOCAL)
# ============================================================================
def generate_embedding(text: str) -> List[float]:
    """Generate a 384-dim embedding using a local model."""
    return model.encode(text).tolist()


# ============================================================================
# PROCESS PDF ENDPOINT
# ============================================================================
@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    """
    1. Extract text from PDF
    2. Chunk it
    3. Generate embeddings
    4. Store in PostgreSQL
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    # Extract + chunk
    text = extract_pdf_text(file.file)
    chunks = chunk_text(text)

    # DB save
    conn = get_db()
    cur = conn.cursor()

    # Insert document metadata
    cur.execute(
        """
        INSERT INTO documents (filename, total_chunks)
        VALUES (%s, %s)
        RETURNING id
        """,
        (file.filename, len(chunks))
    )
    doc_id = cur.fetchone()[0]

    # Insert each chunk into DB
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


# ============================================================================
# SEARCH ENDPOINT (simple semantic search)
# ============================================================================
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
async def search(body: SearchRequest):
    """
    Vector similarity search using pgvector:
    embedding <=> query_embedding
    (lower distance is more similar)
    """
    embedding = generate_embedding(body.query)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT chunk_text,
               1 - (embedding <=> %s::vector) AS score
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (embedding, embedding, body.top_k)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "query": body.query,
        "results": [{"text": r[0], "score": float(r[1])} for r in rows]
    }


# ============================================================================
# RAG + Conversation Memory
# ============================================================================
class AskRequest(BaseModel):
    session_id: str
    question: str
    top_k: int = 5
    include_history: bool = True
    history_limit: int = 10


class AskResponse(BaseModel):
    prompt: str
    retrieved: List[dict]
    session_id: str


# ----------------------
# Message Storage
# ----------------------
def save_message(session_id, role, content):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages (session_id, role, content)
        VALUES (%s, %s, %s)
        """,
        (session_id, role, content)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_recent_messages(session_id: str, limit: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content
        FROM messages
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (session_id, limit)
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Reverse into chronological order
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ----------------------
# Retrieve relevant chunks
# ----------------------
def retrieve_chunks(embedding, top_k):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, document_id, chunk_index, chunk_text,
               1 - (embedding <=> %s::vector) AS score
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (embedding, embedding, top_k)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "document_id": r[1],
            "chunk_index": r[2],
            "text": r[3],
            "score": float(r[4])
        }
        for r in rows
    ]


# ----------------------
# Build RAG prompt
# ----------------------
def build_rag_prompt(instruction, retrieved, history, question):
    prompt = f"SYSTEM: {instruction}\n\n"

    prompt += "RELEVANT DOCUMENTS:\n"
    for i, c in enumerate(retrieved, start=1):
        prompt += f"[DOC {i}] (doc={c['document_id']} idx={c['chunk_index']})\n{c['text']}\n\n"

    if history:
        prompt += "CONVERSATION HISTORY:\n"
        for msg in history:
            prompt += f"{msg['role'].upper()}: {msg['content']}\n"

    prompt += f"\nUSER QUESTION:\n{question}\n"
    prompt += "\nINSTRUCTIONS: Answer using the documents above, cite [DOC X]."

    return prompt


# ============================================================================
# ASK ENDPOINT — main RAG entry point
# ============================================================================
@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """
    NestJS calls this endpoint:
    1. Save user message
    2. Compute embedding
    3. Retrieve relevant chunks
    4. Fetch conversation history
    5. Build RAG prompt
    6. Return prompt → NestJS sends to LLM
    """
    save_message(req.session_id, "user", req.question)

    query_emb = generate_embedding(req.question)
    retrieved = retrieve_chunks(query_emb, req.top_k)
    history = get_recent_messages(req.session_id, req.history_limit) if req.include_history else []

    system_instruction = (
        "You are an AI assistant answering questions strictly using the retrieved documents. "
        "If unsure, say you are unsure. Cite evidence like [DOC 1]."
    )

    prompt = build_rag_prompt(system_instruction, retrieved, history, req.question)

    return AskResponse(prompt=prompt, retrieved=retrieved, session_id=req.session_id)
