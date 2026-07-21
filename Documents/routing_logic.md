# RAG Application — Routing Logic

Two route surfaces, matching the two-runtime split:

1. **Laravel routes** — client-facing (browser/mobile hits these). Owns auth, CRUD, orchestration.
2. **FastAPI routes** — internal only, never hit by the client directly. Laravel calls these server-to-server.

Client never talks to FastAPI. This matters because it's the only place `document_chunk` writes and `document.status` transitions happen, and FastAPI "never authenticates end users directly" per your contract — so there's no route in FastAPI that accepts a user session/token, only a service token.

---

## 1. Laravel Routes — `routes/api.php`

```php
Route::middleware('auth:sanctum')->group(function () {

    // Documents — user's library
    Route::post   ('/documents',                 [DocumentController::class, 'store']);   // upload -> status=uploaded, dispatch EmbedDocumentJob
    Route::get    ('/documents',                  [DocumentController::class, 'index']);
    Route::get    ('/documents/{document}',       [DocumentController::class, 'show']);
    Route::get    ('/documents/{document}/status',[DocumentController::class, 'status']);  // poll target, reads document.status
    Route::delete ('/documents/{document}',       [DocumentController::class, 'destroy']);

    // Chats
    Route::post   ('/chats',                              [ChatController::class, 'store']);
    Route::get    ('/chats',                               [ChatController::class, 'index']);
    Route::get    ('/chats/{chat}',                        [ChatController::class, 'show']);
    Route::post   ('/chats/{chat}/documents',              [ChatController::class, 'attach']);   // writes chat_document
    Route::delete ('/chats/{chat}/documents/{document}',   [ChatController::class, 'detach']);

    // Messages — this is the route that calls FastAPI /query
    Route::post   ('/chats/{chat}/messages', [MsgController::class, 'store']);
    Route::get    ('/chats/{chat}/messages', [MsgController::class, 'index']);
});
```

**No route exists for writing `document_chunk` or setting `document.status` from Laravel's client-facing side** — that would violate the ownership boundary in your contract. Laravel only reads `document.status` (for the poll endpoint) and only writes it implicitly never — FastAPI does that directly against the DB, not through a Laravel route.

---

## 2. FastAPI Routes — internal, service-token gated

```python
# main.py / router

@router.post("/embed")
async def embed_document(
    payload: EmbedRequest,          # { document_id, path }
    _: None = Depends(verify_service_token),
):
    # transitions document.status: uploaded -> chunking -> embedding -> indexed | failed
    ...

@router.post("/query")
async def query(
    payload: QueryRequest,          # { chat_id, message, scoped_document_ids }
    _: None = Depends(verify_service_token),
) -> QueryResponse:                 # { answer, source_chunk_ids }
    ...

@router.get("/health")
async def health():
    return {"status": "ok"}
```

```python
# auth dependency — internal service token, not a user credential
async def verify_service_token(x_service_token: str = Header(...)):
    if not hmac.compare_digest(x_service_token, settings.INTERNAL_SERVICE_TOKEN):
        raise HTTPException(status_code=401, detail="invalid service token")
```

`/embed` and `/query` are the only two endpoints your contract requires. Both reject anything without `X-Service-Token` — there is no user-identity concept on the FastAPI side at all, by design.

---

## 3. Flow A — Document Upload → Indexing

```
Client          Laravel                          FastAPI              Postgres
  │  POST /documents │                                │                    │
  │──────────────────>│ store file, INSERT document      │                    │
  │                   │   status='uploaded'  ────────────────────────────────>│
  │<── 201, document ─│                                │                    │
  │                   │ dispatch(EmbedDocumentJob) [queued, async]           │
  │                   │───── POST /embed {document_id, path} ───────────────>│
  │                   │                                │ UPDATE status=chunking ─>│
  │                   │                                │ UPDATE status=embedding ─>│
  │                   │                                │ INSERT document_chunk(s) ─>│
  │                   │                                │ UPDATE status=indexed | failed ─>│
  │                   │<──────── 200 OK ───────────────│                    │
  │  GET /documents/{id}/status (poll)                 │                    │
  │──────────────────>│ SELECT status ─────────────────────────────────────>│
  │<── {status} ──────│                                │                    │
```

**Why `/embed` is dispatched as a queued job, not a synchronous call in the request cycle**: chunking + embedding a document is not bounded in time — synchronous invocation ties up the HTTP worker and risks client-side timeouts. The Laravel route returns `201` immediately after the `document` row exists; the frontend polls `/status` (or you add a broadcast/websocket event on transition, if you want push instead of poll — not required by the current contract).

```php
// app/Jobs/EmbedDocumentJob.php
class EmbedDocumentJob implements ShouldQueue
{
    public function __construct(private Document $document) {}

    public function handle(): void
    {
        Http::withHeaders(['X-Service-Token' => config('services.rag.token')])
            ->post(config('services.rag.url') . '/embed', [
                'document_id' => $this->document->id,
                'path'        => $this->document->path,
            ])
            ->throw(); // let queue retry policy handle failure
    }
}
```

---

## 4. Flow B — Chat Message → Answer

```
Client          Laravel                          FastAPI              Postgres
  │ POST /chats/{id}/messages {content}               │                    │
  │──────────────────>│ INSERT msg (sender='user') ───────────────────────>│
  │                   │ SELECT document_id FROM chat_document ─────────────>│
  │                   │───── POST /query {chat_id, message, scoped_document_ids} ─>│
  │                   │                                │ SELECT ... <=> ORDER BY distance LIMIT k
  │                   │                                │        WHERE document_id = ANY(scoped_document_ids)
  │                   │                                │ (LLM call, assemble context)
  │                   │<── {answer, source_chunk_ids} ─│                    │
  │                   │ INSERT msg (sender='assistant', content=answer) ───>│
  │                   │ INSERT msg_chunk (msg_id, chunk_id, similarity) ────>│  [one row per source_chunk_id]
  │<── 201, msg ──────│                                │                    │
```

This one **is** synchronous in the request cycle — the client is waiting for an answer, so `MsgController@store` calls FastAPI inline (or via a short-lived queued job + polling/websocket if you want to avoid holding the HTTP connection open through the LLM call latency; either is valid, but the contract's `/query` shape assumes a request/response round trip, not a webhook).

```php
// app/Http/Controllers/MsgController.php (store, abridged)
public function store(Request $request, Chat $chat)
{
    $userMsg = $chat->msgs()->create([
        'sender'  => 'user',
        'content' => $request->input('content'),
        'date'    => now(),
    ]);

    $scopedDocumentIds = $chat->documents()->pluck('document.id');

    $response = Http::withHeaders(['X-Service-Token' => config('services.rag.token')])
        ->post(config('services.rag.url') . '/query', [
            'chat_id'             => $chat->id,
            'message'             => $userMsg->content,
            'scoped_document_ids' => $scopedDocumentIds,
        ])
        ->throw()
        ->json();

    $assistantMsg = $chat->msgs()->create([
        'sender'  => 'assistant',
        'content' => $response['answer'],
        'date'    => now(),
    ]);

    foreach ($response['source_chunk_ids'] as $chunkId) {
        DB::table('msg_chunk')->insert([
            'msg_id'   => $assistantMsg->id,
            'chunk_id' => $chunkId,
            // similarity_score only if /query returns it per chunk
        ]);
    }

    return response()->json($assistantMsg->load('sourceChunks'), 201);
}
```

Note: `msg_chunk` writes happen in Laravel, not FastAPI — matches your contract's "written after receiving `source_chunk_ids`" note. If you want `similarity_score` populated (schema allows it), `/query`'s response needs to return `{chunk_id, similarity_score}` pairs, not bare IDs — decide this before locking the response schema.

---

## 5. Recovery Route — Stuck Pipeline Sweep

Not a client-facing route; a scheduled job on the Laravel side per your contract ("Stuck `chunking`/`embedding` rows → Laravel scheduled job").

```php
// app/Console/Kernel.php
protected function schedule(Schedule $schedule): void
{
    $schedule->job(new SweepStuckDocumentsJob)->everyFiveMinutes();
}

// app/Jobs/SweepStuckDocumentsJob.php
public function handle(): void
{
    Document::whereIn('status', ['chunking', 'embedding'])
        ->where('updated_at', '<', now()->subMinutes(10))
        ->get()
        ->each(function (Document $doc) {
            $doc->update(['status' => 'failed']);
            // optionally: dispatch(new EmbedDocumentJob($doc)); for one retry
        });
}
```

This exists because FastAPI can crash mid-pipeline and there's no other mechanism watching `document.status` for staleness — Laravel owns the schema and the scheduler, so it owns the timeout sweep.

---

## 6. Route Ownership Summary

| Route | Runtime | Caller | Writes |
|---|---|---|---|
| `POST /documents` | Laravel | Client | `document` (status=uploaded) |
| `GET /documents/{id}/status` | Laravel | Client (poll) | none (read) |
| `POST /chats/{id}/messages` | Laravel | Client | `msg` (user), `msg` (assistant), `msg_chunk` |
| `POST /embed` | FastAPI | Laravel (queued job) | `document_chunk`, `document.status` |
| `POST /query` | FastAPI | Laravel (sync, inline) | none (read-only + LLM call) |
| Sweep job | Laravel (cron) | — | `document.status` (failed) |

Two invariants worth keeping in mind as you implement:

- **`/embed` is async, `/query` is sync** — different failure modes. `/embed` failures should retry via queue backoff; `/query` failures should surface to the client immediately (don't silently retry an LLM call that costs money and time on every failure).
- **Nothing in Laravel writes `document_chunk` directly**, even for corrections — if you ever need to edit chunk content, that write still has to go through FastAPI so the embedding gets regenerated (per the "failure mode to watch" note in your schema doc). Don't add a Laravel route that touches that table.
