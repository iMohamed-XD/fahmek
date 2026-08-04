# RAG Application — Data Model (Revised: Single Runtime)

> **Ownership note (updated)**: the two-runtime split (Laravel owns
> migrations, FastAPI owns `document_chunk` writes) no longer applies.
> FastAPI owns the entire schema — all migrations (via Alembic) and all
> writes, including `document_chunk`. The internal rule that *only the
> embed pipeline writes `document_chunk`* still holds, but it's now an
> in-process convention (only call from `embed_document`/the retrieval
> path, never from a route handler directly) rather than something
> structurally enforced by a runtime boundary. See `routing_logic.md` §5.

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

Unchanged from the original design — dropping Laravel doesn't change the
data model, only who implements it. All rationale from the original
revision (chunk-level granularity, removed `ChatLog`, explicit
`chat_document` many-to-many, `document.status` for async tracking,
`password_hash` naming, optional `msg_chunk` for citations) still applies
as written.

## ORM / migrations — SQLAlchemy + Alembic (replaces Eloquent)

```python
# models.py
class DocumentChunk(Base):
    __tablename__ = "document_chunk"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    chunk_index: Mapped[int]
    content: Mapped[str]
    embedding = mapped_column(Vector(384))   # pgvector-sqlalchemy type
    token_count: Mapped[int]
    metadata_: Mapped[dict] = mapped_column("metadata", JSON)
```

The `vector(N)` column still needs a raw migration statement — SQLAlchemy's
`pgvector` integration (the `pgvector` Python package's SQLAlchemy type)
handles the column type in the model, but enabling the extension is still
explicit:

```python
# alembic revision
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("document_chunk", ...)
    op.execute(
        "CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops)"
    )
```

## pgvector implementation notes

1. **Extension:** `CREATE EXTENSION IF NOT EXISTS vector;` — run once per
   database, in the first Alembic migration that creates `document_chunk`.

2. **Dimension (`N`):** must match your embedding model exactly — `384` for
   `multilingual-e5-small`/`bge-small-en-v1.5`, `1536` for
   `text-embedding-3-small`. Fix this before writing the migration —
   changing it later means re-embedding everything and recreating the
   column. This constraint is unchanged by the runtime consolidation.

3. **Index type — pick one, not both:**
   - `ivfflat` — faster to build, needs a `lists` parameter tuned to row
     count, needs `ANALYZE` after bulk inserts.
   - `hnsw` — better recall/latency at query time, no row-count-dependent
     tuning. Preferred past ~100k chunks.

   ```sql
   CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops);
   ```

4. **Distance metric:** cosine (`vector_cosine_ops`) — matches
   `sentence-transformers` models. Don't mix metrics between index and
   query.

5. **Query pattern (now run in-process from the same route handler that
   receives the chat message, not over HTTP to a second runtime):**
   ```sql
   SELECT id, content, embedding <=> :query_embedding AS distance
   FROM document_chunk
   WHERE document_id = ANY(:scoped_document_ids)   -- from chat_document
   ORDER BY distance
   LIMIT :k;
   ```

6. **Failure mode to watch:** inserting a chunk without regenerating its
   embedding after an edit to `content` — nothing enforces that the vector
   matches the text. With the runtime boundary gone, this is even easier to
   violate accidentally (any route handler *can* reach `document_chunk`
   now, where before only FastAPI could reach it at all) — worth an
   explicit code-review rule or a guard in the repository/service layer
   that only the embed pipeline module is allowed to write that table.
