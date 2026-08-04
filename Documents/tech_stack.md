# RAG Application — Tech Stack (Revised: Single Runtime)

## Overview

Single-runtime architecture. FastAPI owns everything: auth, migrations,
CRUD, RAG pipeline (chunking, embedding, retrieval), and async job
dispatch. React + TypeScript is a pure client — it talks to FastAPI over
REST and holds no server-side logic. Laravel is dropped entirely.

```
┌───────────────┐        REST/JSON        ┌───────────────────┐         ┌────────────┐
│ React + TS    │ ──────────────────────> │      FastAPI        │  SQL    │ PostgreSQL │
│ (Vite, RTL)   │ <────────────────────── │  (app + RAG service)│────────>│ + pgvector │
└───────────────┘        JWT auth          └────────┬───────────┘         └─────┬──────┘
                                                    │                            │
                                            enqueue │                            │
                                                    v                            │
                                            ┌───────────────┐                    │
                                            │  arq worker    │────────────────────┘
                                            │ (embed jobs +  │
                                            │  cron sweep)   │
                                            └───────┬────────┘
                                                    │
                                            ┌───────v────────┐
                                            │     Redis      │
                                            └────────────────┘
```

## 1. Application Layer — FastAPI

- **Role**: auth, CRUD, document upload handling, chat endpoints, session
  management, chunking, embedding, retrieval, prompt assembly, LLM calls.
- **Owns**: everything. All migrations (`user`, `document`, `chat`, `msg`,
  `chat_document`, `msg_chunk`, `document_chunk`), all writes, all client-facing
  routes, `document.status` transitions.
- ORM: **SQLAlchemy (async, via `asyncpg`)**. Migrations: **Alembic**.
- No internal/external route split anymore — one route surface, all
  protected by JWT where user-scoped, no service-token layer since there is
  no second runtime to trust.

```python
# models.py (SQLAlchemy, abridged)
class Document(Base):
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    path: Mapped[str]
    status: Mapped[str] = mapped_column(default="uploaded")
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")
```

- `document_chunk.embedding`'s `vector(N)` column is still created via a raw
  Alembic `op.execute(...)` migration since SQLAlchemy doesn't natively model
  the pgvector type either — same rationale as before, different tool.

## 2. Auth — JWT

- **Library**: hand-rolled with `python-jose` (token encode/decode) +
  `passlib[bcrypt]` (password hashing). Chosen deliberately over
  `fastapi-users` to learn the mechanics rather than depend on a framework
  that hides them.
- Access token issued on login, short-lived (e.g. 15–30 min); refresh token
  strategy (rotating refresh token in an httpOnly cookie, or a longer-lived
  JWT) — decide before building the login/refresh endpoints.
- Protects all user-scoped routes via a FastAPI dependency
  (`Depends(get_current_user)`), the direct replacement for `auth:sanctum`
  middleware groups.

## 3. Async Jobs — arq (replaces Laravel's queue)

- **Role**: durable, crash-recoverable execution of `embed_document`, plus a
  cron job replacing the old `SweepStuckDocumentsJob` for documents stuck in
  `chunking`/`embedding`.
- **Why arq over Celery**: arq's job functions are `async def`, matching the
  async SQLAlchemy/`asyncpg` stack directly — no sync/async bridging.
  Operationally lighter for a single free-tier VM (worker + Redis, no beat
  process, no Flower) at the job volume this app actually has.
- Backing store: Redis (new dependency, not present in the old stack).

```python
# worker.py
async def embed_document(ctx, document_id: int, path: str):
    # chunk -> embed -> insert document_chunk rows -> update document.status
    ...

async def sweep_stuck_documents(ctx):
    # status in (chunking, embedding) and updated_at < now() - 10min -> failed
    ...

class WorkerSettings:
    functions = [embed_document]
    cron_jobs = [cron(sweep_stuck_documents, minute=set(range(0, 60, 5)))]
    redis_settings = RedisSettings(host="redis")
```

```python
# route handler, replaces dispatch(new EmbedDocumentJob(...))
@router.post("/documents")
async def upload_document(...):
    document = await create_document(..., status="uploaded")
    await redis_pool.enqueue_job("embed_document", document.id, document.path)
    return document
```

## 4. Embedding Model — sentence-transformers

Unchanged from the two-runtime plan.

**Model choice (pick one, fix `N` before writing the pgvector migration):**

| Model | Dim (`N`) | Notes |
|---|---|---|
| `BAAI/bge-small-en-v1.5` | 384 | Leads MTEB retrieval subsets at its size class; English-focused |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast, widely used baseline |
| `intfloat/multilingual-e5-small` | 384 | Use if Arabic/multilingual content matters |
| OpenAI `text-embedding-3-small` | 1536 | Higher quality, adds API cost + network latency per chunk |

Default recommendation: `multilingual-e5-small` given Arabic is in scope —
local, free, no external API dependency.

**Consequence for the schema**: `document_chunk.embedding` is `vector(384)`.
Changing this later requires re-embedding the entire corpus and recreating
the column — fix it before the first Alembic migration that creates the
table.

## 5. Database — PostgreSQL + pgvector

Unchanged.

- Extension: `CREATE EXTENSION IF NOT EXISTS vector;` — run once, before the
  first migration creating `document_chunk`.
- Index: `hnsw`, cosine distance.

```sql
CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops);
```

## 6. Frontend — React + TypeScript

- **Role**: all UI — auth screens, document library, upload, chat, status
  polling/citations display.
- Build tool: Vite. Styling: Tailwind CSS v4 (`@tailwindcss/vite`,
  CSS-first `@theme {}` config), RTL-first (`dir="rtl"`,
  `rtl:`/`ltr:` variants) — unchanged from prior setup.
- Talks to FastAPI exclusively over REST/JSON; stores the JWT access token
  in memory (not localStorage, to limit XSS exposure) and handles refresh
  via the refresh-token flow.
- No server-rendering, no Blade — this replaces Laravel's entire UI layer.

## 7. Integration Contract (Revised)

| Concern | Owner | Notes |
|---|---|---|
| Schema migrations | FastAPI (Alembic) | Includes `document_chunk` DDL |
| All table writes | FastAPI | No cross-runtime split — one process owns the DB |
| `document.status` transitions | FastAPI (arq worker) | `uploaded → chunking → embedding → indexed/failed` |
| `msg_chunk` (citation) writes | FastAPI | Written in the same request that receives retrieval results — no HTTP round trip to itself |
| Auth | FastAPI (JWT) | No service-token layer — there's no second runtime to authenticate |
| Stuck `chunking`/`embedding` rows | FastAPI (arq cron) | Replaces Laravel's scheduled sweep job |

## Summary Table

| Component | Technology |
|---|---|
| Backend / app / RAG layer | FastAPI (single runtime) |
| ORM / migrations | SQLAlchemy (async) + Alembic |
| Auth | JWT (`python-jose` + `passlib`) |
| Async jobs | arq + Redis |
| Frontend | React + TypeScript (Vite) |
| Styling | Tailwind CSS v4 |
| Embedding model | sentence-transformers (`multilingual-e5-small`) |
| Database | PostgreSQL + pgvector (HNSW, cosine distance) |
