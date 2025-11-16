-- initdb/pg_init.sql
-- Enable pgvector extension and create tables for documents + chunks

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Vector dimension 384 (all-MiniLM-L6-v2). Adjust if you change embedding model.
CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  embedding vector(384)
);

-- ivfflat index (fast approximate search). If it fails in your environment, remove and use sequential scan for dev.
-- This index requires pgvector compiled with ivfflat support.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
  ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
