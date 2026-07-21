# RAG Application — Tech Stack

## Overview

Two-runtime architecture: Laravel handles the application/UI layer and owns
schema migrations; FastAPI handles the RAG pipeline (chunking, embedding,
retrieval) and writes only to `document_chunk`. Both connect to the same
PostgreSQL database.

```
┌─────────────┐         ┌──────────────────┐         ┌────────────┐
│   Laravel   │  HTTP   │     FastAPI       │  SQL    │ PostgreSQL │
│ (Blade UI)  │────────>│  (RAG service)    │────────>│ + pgvector │
│             │<────────│                   │<────────│            │
└──────┬──────┘  JSON   └───────────────────┘         └─────┬──────┘
       │                                                     │
       └─────────── writes user/document/chat/msg ───────────┘
```

## 1. Application Layer — Laravel + Blade + Tailwind

- **Role**: auth, CRUD, document upload handling, chat UI, session management.
- **Owns**: migrations for the full schema (`user`, `document`, `chat`, `msg`,
  `chat_document`, `msg_chunk`, and the DDL for `document_chunk` — but not
  writes to `document_chunk` itself).
- Standard Eloquent relationships map directly onto the schema:

```php
// User model
public function documents() { return $this->hasMany(Document::class); }
public function chats() { return $this->hasMany(Chat::class); }

// Chat model
public function documents() {
    return $this->belongsToMany(Document::class, 'chat_document');
}
public function msgs() { return $this->hasMany(Msg::class); }
```

- `document_chunk`'s `vector(N)` column is created via a raw `DB::statement(...)`
  migration since Eloquent doesn't natively model the pgvector type — but
  Laravel still owns the DDL for versioning/rollback purposes.

## 2. RAG Layer — Python + FastAPI

- **Role**: chunking, embedding generation, similarity search, prompt
  assembly, LLM calls.
- **Owns**: all writes to `document_chunk` (content, embedding, metadata) and
  drives `document.status` transitions (`uploaded → chunking → embedding →
  indexed`/`failed`).
- Connects via `asyncpg` (or similar raw driver) — runs no migrations of its
  own, only reads/writes rows in tables Laravel created.
- Exposes at minimum:
  - `POST /embed` — chunk + embed a document, update status as it progresses.
  - `POST /query` — given `{chat_id, message, scoped_document_ids}`, run the
    `<=>` similarity search scoped by `chat_document`, assemble context, call
    the LLM, return `{answer, source_chunk_ids}`.
- Authenticates via an internal service token from Laravel — never
  authenticates end users directly.

## 3. Embedding Model — sentence-transformers (replaces FastText)

FastText produces static, subword-pooled word embeddings, not contextual
passage embeddings — weak fit for semantic retrieval over 200–800 token
chunks. Replaced with `sentence-transformers`, trained specifically for
semantic passage similarity, which is what the pgvector `<=>` query in the
schema depends on.

**Model choice (pick one, fix `N` before writing the pgvector migration):**

| Model | Dim (`N`) | Notes |
|---|---|---|
| `BAAI/bge-small-en-v1.5` | 384 | Leads MTEB retrieval subsets at its size class; English-focused |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast, widely used baseline |
| `intfloat/multilingual-e5-small` | 384 | Use if Arabic/multilingual content matters |
| OpenAI `text-embedding-3-small` | 1536 | Higher quality, adds API cost + network latency per chunk |

Default recommendation: `bge-small-en-v1.5` (or `multilingual-e5-small` if
Arabic content is in scope) — local, free, no external API dependency,
strong retrieval quality.

**Consequence for the schema**: `document_chunk.embedding` is `vector(384)`,
not the `vector(1536)` used as a placeholder example in `rag_schema.md`.
Changing this later requires re-embedding the entire corpus and recreating
the column — fix it before the first migration.

## 4. Database — PostgreSQL + pgvector

- Extension: `CREATE EXTENSION IF NOT EXISTS vector;` — run once, before the
  first migration creating `document_chunk`.
- Index: `hnsw` preferred over `ivfflat` if chunk count is expected to exceed
  ~100k (no row-count-dependent tuning parameter, better recall/latency at
  query time).

```sql
CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops);
```

- Distance metric: cosine (`vector_cosine_ops`), matching what
  `sentence-transformers` models are optimized for. Don't mix metrics between
  index and query.

## 5. Integration Contract

| Concern | Owner | Notes |
|---|---|---|
| Schema migrations | Laravel | Includes `document_chunk` DDL, not its writes |
| `user`, `chat`, `msg`, `chat_document` writes | Laravel | Conversational/UI state |
| `document_chunk` writes, `document.status` transitions | FastAPI | RAG pipeline internals |
| `msg_chunk` (citation) writes | Laravel | Written after receiving `source_chunk_ids` from FastAPI's `/query` response |
| Auth | Laravel | FastAPI trusts an internal service token, never authenticates end users directly |
| Stuck `chunking`/`embedding` rows | Laravel (scheduled job) | Timeout/retry sweep for documents stuck mid-pipeline if FastAPI crashes |

## Summary Table

| Component | Technology |
|---|---|
| Backend / app layer | Laravel |
| Frontend templating | Blade |
| Styling | Tailwind CSS |
| RAG service | Python + FastAPI |
| Embedding model | sentence-transformers (`bge-small-en-v1.5` or `multilingual-e5-small`) |
| Database | PostgreSQL |
| Vector index | pgvector (HNSW, cosine distance) |
