from fastapi import FastAPI, UploadFile, File, HTTPException # type: ignore
from pypdf import PdfReader # type: ignore
import os
from groq import Groq # type: ignore
import psycopg2 # type: ignore
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ----------------------------
# Connect to PostgreSQL + pgvector
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
# Groq client
# ----------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ----------------------------
# PDF → Text extractor
# ----------------------------
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    if not text.strip():
        raise ValueError("Failed to extract text from PDF")

    return text


# ----------------------------
# Chunking logic
# ----------------------------
def chunk_text(text, max_tokens=300):
    words = text.split()
    chunks = []
    current = []

    for w in words:
        current.append(w)
        if len(current) >= max_tokens:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# ----------------------------
# Embedding generator (Groq)
# ----------------------------
def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )

    return response.data[0].embedding


# ----------------------------
# API: Upload PDF
# ----------------------------
@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    text = extract_pdf_text(file.file)
    chunks = chunk_text(text)

    conn = get_db()
    cur = conn.cursor()

    # Save document meta
    cur.execute(
        "INSERT INTO documents (filename, total_chunks) VALUES (%s, %s) RETURNING id",
        (file.filename, len(chunks))
    )
    doc_id = cur.fetchone()[0]

    # Store chunks + embeddings
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        cur.execute(
            """
            INSERT INTO chunks (doc_id, content, embedding)
            VALUES (%s, %s, %s)
            """,
            (doc_id, chunk, embedding)
        )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "PDF processed",
        "chunks": len(chunks),
        "document_id": doc_id
    }
