# RAG Application — Data Model (Revised)

## Models

```
user
    id              PK
    name            str
    email           str
    password_hash   str
    documents       document[]     (1:many)
    chats           chat[]         (1:many)

document
    id              PK
    name            str
    path            str
    status          enum(uploaded, chunking, embedding, indexed, failed)
    user_id         FK -> user
    chunks          DocumentChunk[]  (1:many)

DocumentChunk
    id              PK
    document_id     FK -> document
    chunk_index     int
    content         text
    embedding       vector(N)         // pgvector column; N = your embedding model's dim
    token_count     int
    metadata        json              // page number, section header, etc.

chat
    id              PK
    user_id         FK -> user
    msgs            msg[]            (1:many)
    documents       document[]       (m:many, via chat_document)

chat_document
    chat_id         FK -> chat
    document_id     FK -> document

msg
    id              PK
    chat_id         FK -> chat
    sender          str              // 'user' | 'assistant'
    content         str
    date            date
    source_chunks   DocumentChunk[]  (m:many, via msg_chunk)   // optional, for citations

msg_chunk           // optional, only needed if you want to show sources per answer
    msg_id          FK -> msg
    chunk_id        FK -> DocumentChunk
    similarity_score float
```

## Relations

```
user            1 : many   document
document        1 : many   DocumentChunk
user            1 : many   chat
chat            1 : many   msg
chat            m : many   document        (via chat_document)
msg             m : many   DocumentChunk   (via msg_chunk)     [optional]
```

## Changes from original schema and why

1. **`document 1:1 MSA_document` → `document 1:many DocumentChunk`**
   Retrieval operates at chunk granularity (200–800 token windows), not whole-document granularity. A single embedding per document loses the precision retrieval depends on. `DocumentChunk.embedding` is a native `vector(N)` column via pgvector.

2. **Removed `ChatLog`**
   `user 1:1 ChatLog 1:many chat` was structurally identical to `user 1:many chat`, since `ChatLog` carried no attributes of its own. Collapsed to a direct FK. Reintroduce `ChatLog` only if it needs to hold something (e.g. per-user chat settings, archival state) — not just to sit between `user` and `chat`.

3. **Made `chat ↔ document` explicit as many-to-many**
   Original schema implied this relation via `Chat.documents[]` but never declared cardinality. Added `chat_document` pivot table: a chat scopes which of the user's library documents are in context for that conversation.

4. **Added `document.status`**
   Chunking/embedding is asynchronous. Without a status field there's no way to know if a document is queryable yet.

5. **`password` → `password_hash`**
   Explicit naming to avoid ambiguity — never store plaintext.

6. **Added optional `msg_chunk` pivot**
   Only needed if you want source citations in the UI (i.e. "this answer was generated from chunks X, Y, Z"). Skip if you don't need traceability.

## pgvector implementation notes

1. **Extension:** `CREATE EXTENSION IF NOT EXISTS vector;` — run once per database, before the first migration that creates `DocumentChunk`.

2. **Dimension (`N`):** must match your embedding model exactly (e.g. 1536 for `text-embedding-3-small`, 3072 for `text-embedding-3-large`, 1024 for many open-source models). Fix this before writing migrations — changing it later means re-embedding everything and recreating the column.

3. **Index type — pick one, not both:**
   - `ivfflat` — faster to build, needs a `lists` parameter tuned to row count (`rows / 1000` as a starting point), and needs `ANALYZE` after bulk inserts or recall degrades.
   - `hnsw` — better recall/latency at query time, slower to build, no row-count-dependent tuning parameter. Preferred if chunk count is expected to grow past ~100k and you don't want to re-tune periodically.

   ```sql
   CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops);
   ```

4. **Distance metric:** match the operator class to what your embedding model was optimized for — almost always cosine (`vector_cosine_ops`) for OpenAI/most sentence-transformer models. L2 (`vector_l2_ops`) is the alternative; don't mix metrics between index and query.

5. **Query pattern:**
   ```sql
   SELECT id, content, embedding <=> :query_embedding AS distance
   FROM document_chunk
   WHERE document_id = ANY(:scoped_document_ids)   -- from chat_document
   ORDER BY distance
   LIMIT :k;
   ```
   Filtering by `document_id` alongside the vector search is what makes the `chat_document` pivot functionally necessary, not just organizational — it scopes retrieval to the documents attached to that chat.

6. **Failure mode to watch:** inserting a chunk without regenerating its embedding after an edit to `content` — nothing enforces that the vector matches the text. If chunk edits are ever allowed, re-embed on write, don't leave it implicit.
