# RAG Application — Routing Logic (Revised: Single Runtime)

One route surface now — FastAPI serves the client (React/TS) directly.
The old Laravel-facing/FastAPI-internal split, and the service-token trust
boundary that existed only because two runtimes had to authenticate each
other, are both gone. Every route below is a normal FastAPI route; the only
distinction left is which ones require a logged-in user (JWT) versus none
(health check).

---

## 1. Routes — `app/routers/`

```python
# routers/documents.py
router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", status_code=201)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: ArqRedis = Depends(get_redis_pool),
):
    document = await create_document(db, user_id=user.id, ..., status="uploaded")
    await redis.enqueue_job("embed_document", document.id, document.path)
    return document

@router.get("")
async def list_documents(user: User = Depends(get_current_user), db=Depends(get_db)):
    return await get_documents_for_user(db, user.id)

@router.get("/{document_id}")
async def get_document(document_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    ...

@router.get("/{document_id}/status")
async def get_document_status(document_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    # poll target, reads document.status — same purpose as before
    ...

@router.delete("/{document_id}")
async def delete_document(document_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    ...
```

```python
# routers/chats.py
router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("")
async def create_chat(user=Depends(get_current_user), db=Depends(get_db)):
    ...

@router.get("")
async def list_chats(user=Depends(get_current_user), db=Depends(get_db)):
    ...

@router.get("/{chat_id}")
async def get_chat(chat_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    ...

@router.post("/{chat_id}/documents")
async def attach_document(chat_id: int, payload: AttachDocumentRequest, user=Depends(get_current_user), db=Depends(get_db)):
    # writes chat_document
    ...

@router.delete("/{chat_id}/documents/{document_id}")
async def detach_document(chat_id: int, document_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    ...

@router.post("/{chat_id}/messages", status_code=201)
async def send_message(
    chat_id: int,
    payload: SendMessageRequest,   # { content }
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_msg = await create_msg(db, chat_id=chat_id, sender="user", content=payload.content)

    scoped_document_ids = await get_scoped_document_ids(db, chat_id)

    # in-process now, not an HTTP call to another runtime
    answer, source_chunks = await run_query(
        db, chat_id=chat_id, message=user_msg.content, scoped_document_ids=scoped_document_ids
    )

    assistant_msg = await create_msg(db, chat_id=chat_id, sender="assistant", content=answer)

    for chunk_id, similarity_score in source_chunks:
        await create_msg_chunk(db, msg_id=assistant_msg.id, chunk_id=chunk_id, similarity_score=similarity_score)

    return assistant_msg

@router.get("/{chat_id}/messages")
async def list_messages(chat_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    ...
```

```python
# routers/auth.py — new, didn't exist on the FastAPI side before
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(payload: RegisterRequest, db=Depends(get_db)):
    ...

@router.post("/login")
async def login(payload: LoginRequest, db=Depends(get_db)):
    # verify password (passlib), issue access + refresh JWT
    ...

@router.post("/refresh")
async def refresh(payload: RefreshRequest):
    ...
```

```python
@router.get("/health")
async def health():
    return {"status": "ok"}
```

**What's gone**: no `X-Service-Token` header, no `verify_service_token`
dependency, no distinction between "client-facing" and "internal" routers.
`get_current_user` (JWT dependency) is the only auth gate, and it's absent
only from `/auth/*` and `/health`.

---

## 2. Flow A — Document Upload → Indexing

```
Client              FastAPI                         arq worker           Postgres
  │ POST /documents  │                                                        │
  │──────────────────>│ INSERT document (status='uploaded') ────────────────>│
  │                   │ enqueue_job('embed_document', id, path)               │
  │<── 201, document ─│                                                        │
  │                   │                    ┌──── picks up job ────┐          │
  │                   │                    │ UPDATE status=chunking ────────>│
  │                   │                    │ UPDATE status=embedding ───────>│
  │                   │                    │ INSERT document_chunk(s) ──────>│
  │                   │                    │ UPDATE status=indexed|failed ──>│
  │ GET /documents/{id}/status (poll)      └───────────────────────┘          │
  │──────────────────>│ SELECT status ─────────────────────────────────────>│
  │<── {status} ──────│                                                        │
```

The reasoning for async dispatch is unchanged — chunking + embedding isn't
bounded in time, so it shouldn't hold an HTTP worker. Only the mechanism
changed: `redis.enqueue_job(...)` replaces `dispatch(new EmbedDocumentJob)`.

---

## 3. Flow B — Chat Message → Answer

```
Client              FastAPI                                              Postgres
  │ POST /chats/{id}/messages {content}                                     │
  │──────────────────>│ INSERT msg (sender='user') ───────────────────────>│
  │                   │ SELECT document_id FROM chat_document ─────────────>│
  │                   │ SELECT ... <=> ORDER BY distance LIMIT k             │
  │                   │        WHERE document_id = ANY(scoped_document_ids) │
  │                   │ (LLM call, assemble context) — in-process, no       │
  │                   │  second-runtime round trip                          │
  │                   │ INSERT msg (sender='assistant', content=answer) ───>│
  │                   │ INSERT msg_chunk (msg_id, chunk_id, similarity) ────>│
  │<── 201, msg ──────│                                                        │
```

This stays synchronous in the request cycle for the same reason as before —
the client is waiting on an answer. The only change is that retrieval,
generation, and the `msg_chunk` write all happen as function calls inside
one process instead of an HTTP call to a second runtime followed by a
response parse. This removes an entire failure class (network errors
between Laravel and FastAPI, response-shape mismatches on
`source_chunk_ids`) — the `/query` response-contract question
(`source_chunk_ids` vs. `{chunk_id, similarity_score}` pairs) is now moot
since there's no serialization boundary between retrieval and the
`msg_chunk` write; pass the tuple directly.

---

## 4. Recovery — Stuck Pipeline Sweep

Replaces the Laravel scheduled job with an arq cron job — same trigger
condition, runs inside the same worker process that executes `embed_document`.

```python
async def sweep_stuck_documents(ctx):
    async with get_db_session() as db:
        stuck = await get_documents_with_status_older_than(
            db, statuses=["chunking", "embedding"], older_than_minutes=10
        )
        for doc in stuck:
            await update_document_status(db, doc.id, status="failed")
            # optionally: await ctx["redis"].enqueue_job("embed_document", doc.id, doc.path)

class WorkerSettings:
    functions = [embed_document]
    cron_jobs = [cron(sweep_stuck_documents, minute=set(range(0, 60, 5)))]
```

---

## 5. Route Ownership Summary

| Route | Auth | Writes |
|---|---|---|
| `POST /auth/register`, `/auth/login`, `/auth/refresh` | none | `user` |
| `POST /documents` | JWT | `document` (status=uploaded), enqueues `embed_document` |
| `GET /documents/{id}/status` | JWT | none (read) |
| `POST /chats/{id}/messages` | JWT | `msg` (user), `msg` (assistant), `msg_chunk` |
| `embed_document` (arq job) | service-internal (not an HTTP route) | `document_chunk`, `document.status` |
| `sweep_stuck_documents` (arq cron) | service-internal | `document.status` (failed) |

Two invariants carried over unchanged:

- **`embed_document` is async (queued), the chat-message flow is sync** —
  same reasoning as before, just a different queue mechanism.
- **Only `embed_document` writes `document_chunk`.** Route handlers still
  must not touch that table directly, even now that there's no cross-runtime
  boundary enforcing it structurally — re-embedding on edit is still the
  rule, just enforced by convention/code review instead of a process
  boundary. Worth a comment in the model or a DB-level check if you want it
  enforced more strictly than "don't do that."
