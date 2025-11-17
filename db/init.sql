CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    total_chunks INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
