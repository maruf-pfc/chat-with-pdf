# Chat with PDF

## Flow Diagram

```txt
[User uploads PDFs]
      ↓
Next.js UI → NestJS → Python Worker → DB (documents/chunks)

[User asks questions]
      ↓
Next.js → NestJS → Python Worker → (returns RAG prompt)
      ↓
NestJS → LLM (OpenAI/Groq/local) → Final Answer
      ↓
Next.js displays chat history
```