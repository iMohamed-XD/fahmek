# Fahemak (فاهمك) — Comprehensive Repository & Architecture Analysis

> **Document Status**: Complete Architectural & Codebase Audit  
> **Target System**: Fahemak (فاهمك) — Arabic-First RAG Document Understanding System  
> **Audited Date**: August 2026  
> **Repository Path**: `c:\Python PRACTICE\fahmek`  

---

## Executive Summary & System Overview

**Fahemak (فاهمك)** is an Arabic-first Retrieval-Augmented Generation (RAG) web application designed for intelligent document understanding, semantic search, and contextual chat interactions.

The project is designed as a **Single-Runtime Architecture**:
1. **Backend**: FastAPI (Python 3.12) owning Auth, REST APIs, Database Migrations (Alembic), SQLAlchemy Async ORM, and the full RAG pipeline (chunking, embedding, vector retrieval via pgvector, and LLM prompt synthesis).
2. **Database**: PostgreSQL 16 equipped with the `pgvector` extension for storing 384-dimensional dense vector embeddings with HNSW indexing and cosine similarity matching.
3. **Frontend**: A client-side React 19 + TypeScript application built with Vite and Tailwind CSS v4, operating as a pure REST client (storing short-lived JWT access tokens in memory).

---

## 1. Project Directory Structure Mapping

```
fahmek/
├── .gitignore
├── README.md                            # Basic docker-compose startup instructions
├── docker-compose.yml                   # Production-like multi-container compose file
├── docker-compose.override.yml          # Local dev override with Uvicorn hot-reloading
├── Documents/                           # Architecture specs, design system, and schemas
│   ├── FrontEnd_structure.md            # Target React folder structure & rules
│   ├── fahemak_design_system.md         # Color tokens (Green/Gold/Neutral) & Icon specs
│   ├── logo.png                         # Master logo asset
│   ├── rag_schema.md                    # Database entities, relationships & pgvector spec
│   ├── routing_logic.md                 # API endpoints, request flows & auth gates
│   └── tech_stack.md                    # Single-runtime architectural mandate
├── frontend/                            # React 19 + TypeScript + Vite SPA
│   ├── .gitignore
│   ├── eslint.config.js
│   ├── index.html                       # HTML entry point (#root)
│   ├── package.json                     # Node dependencies (React 19, Tailwind v4)
│   ├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
│   ├── vite.config.ts                   # Vite configuration with @tailwindcss/vite
│   └── src/                             # Frontend source code
│       ├── App.css
│       ├── App.tsx                      # Root component (Current: Vite default placeholder)
│       ├── index.css                    # Tailwind CSS v4 entry (@import "tailwindcss")
│       ├── main.tsx                     # React DOM root mounting script
│       ├── api/                         # [EMPTY] Target REST API contract functions
│       ├── app/                         # [EMPTY] Target App router & context providers
│       ├── assets/                      # Static assets
│       ├── components/                  # UI Primitives & Layout
│       │   ├── icons/                   # [EMPTY] Tabler icons & RTL mirror helpers
│       │   ├── layout/                  # [EMPTY] AppShell, Header, Sidebar
│       │   └── ui/                      # [EMPTY] Buttons, Inputs, Modals, Badges
│       ├── constants/                   # [EMPTY] Route paths, status enums
│       ├── contexts/                    # [EMPTY] Global state contexts
│       ├── features/                    # Feature modules
│       │   ├── auth/                    # Auth forms, context, hooks
│       │   ├── chat/                    # Chat window, message bubbles, citations
│       │   └── documents/               # File upload, document list, status badge
│       ├── hooks/                       # [EMPTY] Generic hooks (useDebounce, etc.)
│       ├── lib/                         # [EMPTY] Utility helpers (cn, formatters)
│       ├── pages/                       # [EMPTY] Screen views (Login, Chat, Documents)
│       ├── services/                    # [EMPTY] Auxiliary services
│       ├── styles/                      # [EMPTY] Target theme custom properties
│       ├── types/                       # [EMPTY] Shared TypeScript interfaces
│       └── utils/                       # [EMPTY] Utility functions
└── RAG_service/                         # FastAPI Backend Application
    ├── .dockerignore
    ├── .env / .env.example
    ├── .gitignore
    ├── Dockerfile                       # Multi-stage Docker build (uv -> slim runtime)
    ├── RAG.py                           # Standalone CLI RAG prototype script (LangChain + Chroma)
    ├── README.md
    ├── alembic.ini                      # Alembic database migration config
    ├── pyproject.toml                   # uv / PEP 621 package dependencies & lock target
    ├── requirements.txt                 # Exported pip requirements list
    ├── sqlite.db                        # Legacy SQLite database file
    ├── uv.lock                          # Dependency lock file
    ├── alembic/                         # Migration scripts
    │   ├── env.py                       # Async Alembic execution runner
    │   ├── script.py.mako               # Template for migration generation
    │   └── versions/
    │       └── 5f54e4d624f8_create_initial_tables.py # Initial DB tables & pgvector setup
    ├── app/                             # Core FastAPI application module
    │   ├── __init__.py
    │   ├── config.py                    # BaseSettings environment configuration
    │   ├── main.py                      # FastAPI app initialization, lifespan & router mounting
    │   ├── schemas.py                   # Pydantic v2 DTO schemas
    │   ├── api/                         # API Router Layer
    │   │   ├── Chats/                   # Chat router sub-package
    │   │   │   ├── chatRouter.py        # [EMPTY (0 bytes)] Chat endpoints
    │   │   │   └── dependencies.py      # [EMPTY (0 bytes)] Chat dependencies
    │   │   ├── Documents/               # Document router sub-package
    │   │   │   ├── dependencies.py      # DocumentService dependency provider
    │   │   │   └── documentRouter.py    # Document CRUD endpoints
    │   │   ├── Msgs/                    # Message router sub-package
    │   │   │   ├── dependencies.py      # [EMPTY (0 bytes)] Message dependencies
    │   │   │   └── msgRouter.py         # [EMPTY (0 bytes)] Message endpoints
    │   │   └── Users/                   # User & Auth sub-package
    │   │       ├── dependencies.py      # UserService & OAuth2 get_current_user dependencies
    │   │       └── userRouter.py        # /users register, login, refresh, logout, me
    │   ├── core/                        # Core Utilities & Security
    │   │   ├── auth.py                  # JWT encoding/decoding, passlib password hashing
    │   │   └── config.py                # [EMPTY (0 bytes)] Auxiliary config file
    │   ├── db/                          # Database Infrastructure
    │   │   ├── factory.py               # Document factory boy test data generator
    │   │   ├── models.py                # SQLAlchemy Declarative Models (User, Document, etc.)
    │   │   ├── queries.py               # [EMPTY (0 bytes)] Raw query helper module
    │   │   └── session.py               # Async Engine, AsyncSession generator, create_db()
    │   ├── llm/                         # LLM Provider Integration
    │   │   └── client.py                # ChatGoogleGenerativeAI (Gemini) initializer
    │   ├── pipeline/                    # RAG Pipeline Subsystem
    │   │   ├── chuncking.py             # [EMPTY (0 bytes)] Text splitting logic
    │   │   ├── embedding.py             # [EMPTY (0 bytes)] Sentence-transformers embedder
    │   │   └── retrieval.py             # [EMPTY (0 bytes)] Vector search queries
    │   ├── routers/                     # Auxiliary Routers
    │   │   ├── embed.py                 # [EMPTY (0 bytes)]
    │   │   └── query.py                 # [EMPTY (0 bytes)]
    │   └── services/                    # Business Service Layer
    │       ├── chat.py                  # [EMPTY (0 bytes)] Chat business logic
    │       ├── document.py              # Document CRUD & management logic
    │       ├── msg.py                   # [EMPTY (0 bytes)] Message & retrieval orchestration
    │       └── user.py                  # User management & auth business logic
    └── scripts/
        ├── __init__.py
        └── seed.py                      # Database seeder script
```

---

## 2. Architecture & Component Dependency Map

The overall system architecture follows a clean 3-tier model with asynchronous database operations and a vector search pipeline.

```mermaid
graph TD
    Client[React + TypeScript SPA<br/>Vite / Tailwind CSS v4] -->|HTTP REST + Bearer JWT| FastAPI[FastAPI Server<br/>app.main:app]
    
    subgraph FastAPI Application
        FastAPI --> AuthMiddleware[OAuth2 / JWT Auth Gate<br/>app.core.auth]
        FastAPI --> UserRouter[/users Router<br/>app.api.Users]
        FastAPI --> DocRouter[/documents Router<br/>app.api.Documents]
        FastAPI --> ChatRouter[/chats Router<br/>app.api.Chats - Pending]
        
        UserRouter --> UserService[UserService<br/>app.services.user]
        DocRouter --> DocService[DocumentService<br/>app.services.document]
        
        UserService --> SQLAlchemy[Async SQLAlchemy ORM<br/>app.db.models]
        DocService --> SQLAlchemy
        
        RAGPipeline[RAG Pipeline<br/>app.pipeline - Pending] --> SentenceTransformers[Sentence-Transformers<br/>multilingual-e5-small]
        RAGPipeline --> GeminiAPI[LangChain + Gemini API<br/>app.llm.client]
        RAGPipeline --> SQLAlchemy
    end
    
    SQLAlchemy -->|asyncpg driver| PostgreSQL[(PostgreSQL 16 + pgvector<br/>HNSW Cosine Distance)]
```

### Component Interdependencies
1. **Frontend → Backend**: SPA communicates with FastAPI over REST/JSON. Requests requiring user scope pass a `Bearer <access_token>` in the `Authorization` header.
2. **Routers → Services**: FastAPI route functions (`userRouter.py`, `documentRouter.py`) accept injected service dependencies (`UserService`, `DocumentService`). Routers contain no SQL queries or business rules; they validate inputs and delegate work.
3. **Services → Models & Auth**: `UserService` relies on `app.core.auth` for password hashing (`bcrypt`) and token generation, executing CRUD via SQLAlchemy `AsyncSession`.
4. **ORM → Database**: `app.db.session` manages the async engine connected to PostgreSQL via `asyncpg`. Migrations are driven by Alembic using SQLAlchemy metadata.
5. **RAG Subsystem → Vector Store**: Document chunks are stored in `document_chunk` with an embedding column of type `Vector(384)`. Vector queries execute cosine similarity distance checks (`embedding <=> :query_vector`).

---

## 3. Entry Points Analysis

| Component / Script | Location | Purpose & Execution Flow |
|---|---|---|
| **FastAPI Backend Entry** | `RAG_service/app/main.py` | Instantiates `FastAPI(title="...", lifespan=lifespan)`. The lifespan function executes `create_db()` on startup to ensure `CREATE EXTENSION IF NOT EXISTS vector;` runs. Includes `UserRouter`, `DocumentRouter`, `/health`, and `/scalar` documentation. |
| **Docker Compose Entry** | `docker-compose.yml` | Spawns `postgres` (`pgvector/pgvector:pg16`) and `backend` (FastAPI container on port 8000). Uses `docker-compose.override.yml` in dev to mount `./RAG_service/app` for live Uvicorn reloading. |
| **Backend Container Entry** | `RAG_service/Dockerfile` | Multi-stage build using `python:3.12-slim` and Astral `uv`. Final CMD runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Includes healthcheck script hitting `/health`. |
| **Alembic Engine Entry** | `RAG_service/alembic/env.py` | Migration entry point. Dynamically injects `DATABASE_URL` from `app.config.settings` and executes async migrations using `async_engine_from_config`. |
| **Frontend SPA Entry** | `frontend/src/main.tsx` | React 19 client entry point. Mounts `App.tsx` into DOM node `#root` with `<StrictMode>`. |
| **Standalone Prototype Entry** | `RAG_service/RAG.py` | Isolated CLI script demonstration of a LangChain RAG pipeline using ChromaDB, `GoogleGenerativeAIEmbeddings`, and Gemini 2.5 Flash over a local handbook file. *Not hooked into the web application.* |

---

## 4. Database Layer & Models

### Connection & Session Management
Defined in `RAG_service/app/db/session.py`:
* **Async Engine**: Built via `create_async_engine(settings.DATABASE_URL, echo=True)` utilizing the `postgresql+asyncpg` driver scheme.
* **Session Dependency**: `get_session()` yields an `AsyncSession` bound to an `async_sessionmaker(expire_on_commit=False)`.

### Database Schema & SQLAlchemy Models
Defined in `RAG_service/app/db/models.py`:

```
┌─────────────────────────┐        1:N        ┌─────────────────────────┐        1:N        ┌───────────────────────────────┐
│          User           │ ─────────────────>│        Document         │ ─────────────────>│         DocumentChunk         │
├─────────────────────────┤                   ├─────────────────────────┤                   ├───────────────────────────────┤
│ id: int (PK)            │                   │ id: int (PK)            │                   │ id: int (PK)                  │
│ name: str               │                   │ name: str               │                   │ document_id: int (FK)         │
│ email: str (UQ, IX)     │                   │ path: str               │                   │ chunk_index: int              │
│ password_hash: str      │                   │ status: DocumentStatus  │                   │ content: str                  │
│ token_version: int      │                   │ user_id: int (FK)       │                   │ embedding: Vector(384)        │
└─────────────────────────┘                   └─────────────────────────┘                   │ token_count: int              │
             │                                             │                                │ metadata_: dict (JSON)        │
             │ 1:N                                         │ N:M (via chat_document)        └───────────────────────────────┘
             v                                             v                                                ▲
┌─────────────────────────┐                   ┌─────────────────────────┐                                   │
│          Chat           │                   │      chat_document      │                                   │ N:M
├─────────────────────────┤                   ├─────────────────────────┤                                   │ (via msg_chunk)
│ id: int (PK)            │                   │ chat_id: int (PK, FK)   │                                   │
│ user_id: int (FK)       │                   │ document_id: (PK, FK)   │                                   │
└─────────────────────────┘                   └─────────────────────────┘                                   │
             │                                                                                              │
             │ 1:N                                                                                          │
             v                                                                                              │
┌─────────────────────────┐        1:N        ┌─────────────────────────┐                                   │
│           Msg           │ ─────────────────>│        MsgChunk         │ ────────────────────────────────────┘
├─────────────────────────┤                   ├─────────────────────────┤
│ id: int (PK)            │                   │ msg_id: int (PK, FK)    │
│ chat_id: int (FK)       │                   │ chunk_id: int (PK, FK)  │
│ sender: str             │                   │ similarity_score: float │
│ content: str            │                   └─────────────────────────┘
│ date: datetime          │
└─────────────────────────┘
```

1. **`User`**: Core user record. Stores hashed passwords (`password_hash`) and a `token_version` integer used for instant refresh token revocation across devices.
2. **`Document`**: Represents an uploaded file. Tracks processing pipeline state via `DocumentStatus` enum (`uploaded` → `chunking` → `embedding` → `indexed` / `failed`). Linked to `User`.
3. **`DocumentChunk`**: Stores document segments. Contains `content`, `token_count`, arbitrary `metadata_` (page numbers, section titles), and `embedding` defined as `Vector(384)` using `pgvector.sqlalchemy`.
4. **`Chat`**: A user chat session linked to `User`.
5. **`chat_document`**: Many-to-Many association table scoping specific `Document` instances to a `Chat`.
6. **`Msg`**: Message log within a chat session (`sender` = `'user'` or `'assistant'`).
7. **`MsgChunk`**: Citation association table linking assistant messages to exact source `DocumentChunk` instances with a stored `similarity_score`.

---

## 5. Pydantic Schemas (Data Transfer Objects)

Defined in `RAG_service/app/schemas.py`:

* **User Schemas**:
  * `UserCreate`: `name`, `email` (validated via `EmailStr`), `password` (plaintext in, hashed before persistence).
  * `UserRead`: `id`, `name`, `email` (`from_attributes=True` for SQLAlchemy serialization).
  * `UserUpdate`: Optional `name`, `email`.
* **Auth Schemas**:
  * `Token`: `access_token`, `refresh_token`, `token_type` (default `"bearer"`).
  * `RefreshRequest`: `refresh_token` payload.
* **Document Schemas**:
  * `DocumentCreate`: `name` (file metadata). Server assigns `path`, `status`, and `user_id`.
  * `DocumentRead`: `id`, `name`, `status`, `user_id`.
  * `DocumentUpdate`: Optional `name`, `status`.
* **Message Schemas**:
  * `MsgCreate`: `content`.
  * `MsgRead`: `id`, `chat_id`, `sender`, `content`, `date`.

---

## 6. Business Service Layer & Services

### 1. `UserService` (`RAG_service/app/services/user.py`)
* **`create_user(data)`**: Checks for email conflicts (case-insensitive via `.lower()`), hashes password with bcrypt, persists `User`.
* **`authenticate(email, password)`**: Fetches user by email. **Timing Attack Protection**: If the user is not found, executes `verify_password` against a precomputed `_DUMMY_HASH` to ensure identical CPU execution time and prevent user-enumeration side channels.
* **`bump_token_version(user)`**: Increments `user.token_version`, invalidating all existing refresh tokens.
* **`get_user_by_email` / `update_user`**: Data retrieval and mutation.

### 2. `DocumentService` (`RAG_service/app/services/document.py`)
* **`get_document_field(id, field)`**: Validates field name against `DocumentRead` model fields and returns property value.
* **`create_document(data, user_id, path)`**: Instantiates and persists a `Document`.
* **`delete_document(id)`**: Removes document record.
* **`update_document(id, data)`**: *Contains a known bug* (calls `.sqlmodel_update()` on a pure SQLAlchemy model).

### 3. Unfinished / Empty Services
* `chat.py` (0 bytes): Pending chat creation and document attachment logic.
* `msg.py` (0 bytes): Pending message orchestration and RAG retrieval invocation.

---

## 7. API Routes & Router Layer

### Active Endpoints Summary

| HTTP Method | Route Endpoint | Auth Required | Router File | Description |
|---|---|---|---|---|
| `GET` | `/health` | No | `app/main.py` | Health check returning `{"status": "ok"}` |
| `GET` | `/scalar` | No | `app/main.py` | Interactive Scalar API Documentation |
| `POST` | `/users/register` | No | `userRouter.py` | Registers a new user account |
| `POST` | `/users/login` | No | `userRouter.py` | Authenticates via OAuth2 Form, returns Access & Refresh JWTs |
| `POST` | `/users/refresh` | No | `userRouter.py` | Validates refresh token & version, issues new token pair |
| `POST` | `/users/logout` | JWT | `userRouter.py` | Revokes refresh tokens by bumping token version |
| `GET` | `/users/me` | JWT | `userRouter.py` | Returns current user profile |
| `GET` | `/documents/{id}` | No (Bug) | `documentRouter.py` | Retrieves document by ID |
| `GET` | `/documents/{id}/{field}`| No (Bug) | `documentRouter.py` | Retrieves specific document property |
| `POST` | `/documents/` | No (Bug) | `documentRouter.py` | Creates document record |
| `PUT` / `PATCH`| `/documents/` | No (Bug) | `documentRouter.py` | Updates document record |
| `DELETE` | `/documents/{id}` | No (Bug) | `documentRouter.py` | Deletes document record |

*Note: As detailed in Section 11, the `/documents` endpoints are currently missing the `currentUserDep` JWT auth guard.*

---

## 8. Dependencies & Configuration

### Environment Variables (`RAG_service/app/config.py`)
Managed via Pydantic `BaseSettings` reading `./.env`:
* `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`: PostgreSQL database credentials.
* `DATABASE_URL` (Property): Computes `postgresql+asyncpg://...` connection string dynamically.
* `JWT_SECRET_KEY`, `JWT_ALGORITHM` (Default `"HS256"`): Security token keys.
* `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `WEATHER_API_KEY`: External service keys.
* `APP_NAME`, `APP_HOST`, `APP_PORT`: Server settings.

### Package Management (`pyproject.toml`)
* Built with Astral `uv`.
* Core packages: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `alembic`, `pgvector`, `python-jose`, `passlib[bcrypt]`, `arq`, `redis`, `sentence-transformers`, `langchain-google-genai`.

---

## 9. Authentication & Security Architecture

The application implements standard Stateless JWT Authentication with Refresh Token Revocation:

```
[ Client ]                                   [ FastAPI Auth Layer ]                      [ UserService / DB ]
    │                                                   │                                        │
    │ ─── 1. POST /users/login (username, password) ──> │                                        │
    │                                                   │ ─── 2. Authenticate User ─────────────> │ (Check bcrypt hash)
    │ <── 3. Return { access_token, refresh_token } ─── │                                        │
    │                                                   │                                        │
    │ ─── 4. Request Protected Route (Header: Bearer) ─> │                                        │
    │                                                   │ ─── 5. decode_token(token)             │
    │                                                   │      Check: exp, type=='access'        │
    │                                                   │ ─── 6. Fetch User by sub ID ──────────> │
    │ <── 7. Execute Route Handler & Return Data ────── │                                        │
```

1. **Password Security**: Passwords are hashed using `bcrypt` via `passlib.context.CryptContext`.
2. **Access Tokens**: Short-lived (20 minutes). Payload contains `sub` (User ID string) and `type: "access"`.
3. **Refresh Tokens**: Long-lived (7 days). Payload contains `sub`, `ver` (`token_version`), and `type: "refresh"`.
4. **Token Revocation Mechanism**: `User.token_version` starts at `0`. When `/users/refresh` is hit, the system verifies `payload["ver"] == user.token_version`. Hitting `/users/logout` executes `bump_token_version()`, incrementing `token_version` in the DB and immediately invalidating all outstanding refresh tokens globally.

---

## 10. Request Flow Execution Trace

Here is the step-by-step lifecycle of an authenticated HTTP request (e.g., `GET /users/me`):

```
[ HTTP Request ] 
       │  Header: Authorization: Bearer <JWT_ACCESS_TOKEN>
       ▼
[ Uvicorn ASGI Server ]
       │  Parses HTTP bytes -> passes ASGI Scope dict to FastAPI app instance
       ▼
[ FastAPI APIRouter: /users/me ]
       │  Triggered by matching path and HTTP method
       ▼
[ Dependency Injection: get_current_user ] (in app.api.Users.dependencies)
       │  1. OAuth2PasswordBearer extracts token string from Authorization header
       │  2. Calls app.core.auth.decode_token(token)
       │  3. Validates JWT signature with JWT_SECRET_KEY and checks expiration (exp)
       │  4. Asserts payload["type"] == "access"
       │  5. Extracts user_id from payload["sub"]
       │  6. Injects get_user_service dependency -> instantiates UserService(AsyncSession)
       │  7. Calls await service.get_user(int(user_id))
       ▼
[ Service & Database Layer ]
       │  UserService executes: await self.session.get(User, user_id)
       │  AsyncSession dispatches SQL over asyncpg connection pool:
       │  --> SELECT user.id, user.name, user.email, user.password_hash, user.token_version FROM "user" WHERE user.id = $1
       │  PostgreSQL returns user row -> SQLAlchemy instantiates User ORM model
       ▼
[ Route Handler Execution: get_me ] (in app.api.Users.userRouter)
       │  Receives validated User ORM object as current_user parameter
       │  Executes: UserRead.model_validate(current_user)
       │  Pydantic filters out password_hash and token_version
       ▼
[ HTTP Response Serialization ]
       │  FastAPI serializes UserRead Pydantic model to JSON:
       │  {"id": 1, "name": "Mohamed", "email": "mohamed@example.com"}
       │  Sets HTTP Status Code 200 OK, Content-Type: application/json
       ▼
[ Client ]
```

---

## 11. Specifications vs. Implementation Gap Analysis

Comparing the codebase against the architectural specifications in `Documents/`:

| Spec Requirement | Document Reference | Current Status in Codebase | Action Required |
|---|---|---|---|
| **Single-Runtime Architecture** | `tech_stack.md` §1 | **Partial**. FastAPI project configured, but major backend routes/services are unbuilt. | Complete RAG routes and business services. |
| **Database Schema** | `rag_schema.md` | **Complete**. All 7 tables (`user`, `document`, `document_chunk`, `chat`, `chat_document`, `msg`, `msg_chunk`) defined in SQLAlchemy and migrated via Alembic. | None. DB schema is ready. |
| **pgvector Indexing** | `rag_schema.md` §3 | **Partial**. `vector` extension created and `Vector(384)` column added, but HNSW index (`CREATE INDEX ON document_chunk USING hnsw...`) is missing from Alembic migration. | Add HNSW index to Alembic migration. |
| **Auth System** | `routing_logic.md` §1 | **Complete for Users**. `/users/register`, `/login`, `/refresh`, `/logout`, `/me` implemented with timing attack defense. | Attach `currentUserDep` to Document and Chat routers. |
| **Async Worker (arq + Redis)** | `tech_stack.md` §3 | **Missing**. `arq` is in `pyproject.toml`, but no `worker.py` or Redis connection is implemented for background document embedding. | Implement `app/worker.py` for chunking/embedding. |
| **RAG Pipeline (Chunk/Embed/Retrieve)**| `tech_stack.md` §4 | **Missing / Empty Files**. `chuncking.py`, `embedding.py`, `retrieval.py` are all 0 bytes. | Build text chunker, sentence-transformers embedder, and pgvector cosine query runner. |
| **Chat & Message Routers** | `routing_logic.md` §1 | **Missing / Empty Files**. `chatRouter.py` and `msgRouter.py` are 0 bytes. | Build `/chats` and `/chats/{id}/messages` handlers. |
| **Frontend Setup** | `FrontEnd_structure.md` | **Scaffold Only**. Vite + React 19 + Tailwind v4 configured, but all feature modules, API clients, and UI components are unbuilt. | Implement design tokens, auth context, document manager, and chat interface. |

---

## 12. File-by-File Breakdown

### Root Directory
* **`docker-compose.yml`**: Configures multi-container setup for `postgres` (`pgvector/pgvector:pg16`) on port `5432` and `backend` on port `8000`. Includes healthchecks.
* **`docker-compose.override.yml`**: Mounts `./RAG_service/app` into container `/app/app` and enables Uvicorn `--reload` mode for development.
* **`README.md`**: Contains minimal setup CLI commands (`docker compose up -d --build`, `alembic upgrade head`).

### `Documents/` Directory
* **`tech_stack.md`**: Architectural vision document establishing the FastAPI single-runtime model and arq/Redis background worker design.
* **`rag_schema.md`**: Database schema specification detailing table relationships and pgvector configuration.
* **`routing_logic.md`**: Router specifications detailing endpoints, payload shapes, and request flows.
* **`FrontEnd_structure.md`**: Comprehensive design document outlining target React folder structure, API abstraction rules, and feature colocation.
* **`fahemak_design_system.md`**: Color token specification (Green `--green-200` #C0DD97, Gold `--gold-400` #EF9F27, status colors) and icon choices (Tabler icons, RTL mirror rules).

### `RAG_service/` Backend
* **`RAG_service/pyproject.toml`**: Dependency definition file for Astral `uv`. Specifies Python 3.12+, FastAPI, SQLAlchemy, asyncpg, Alembic, pgvector, arq, sentence-transformers, and LangChain.
* **`RAG_service/Dockerfile`**: Two-stage slim Docker image build utilizing `uv` for reproducible environment installation.
* **`RAG_service/RAG.py`**: Standalone RAG CLI prototype using ChromaDB and Gemini. *Reference code only*.
* **`RAG_service/app/main.py`**: Application factory and entry point. Sets up lifespan DB setup, mounts routers, and defines `/health` and `/scalar` documentation routes.
* **`RAG_service/app/config.py`**: Pydantic `BaseSettings` loader for environment variables (`DATABASE_URL`, JWT secret, etc.).
* **`RAG_service/app/schemas.py`**: Pydantic DTOs for Users, Tokens, Documents, and Messages.
* **`RAG_service/app/core/auth.py`**: JWT creation/decoding (`python-jose`) and password hashing (`passlib` bcrypt).
* **`RAG_service/app/db/models.py`**: Declarative SQLAlchemy models (`User`, `Document`, `DocumentChunk`, `Chat`, `chat_document`, `Msg`, `MsgChunk`, `DocumentStatus`).
* **`RAG_service/app/db/session.py`**: Async SQLAlchemy database engine setup and `get_session()` dependency generator.
* **`RAG_service/app/db/factory.py`**: Factory-boy generator for document test data (*references outdated schema*).
* **`RAG_service/app/services/user.py`**: User management service with timing-attack resistant authentication and token invalidation.
* **`RAG_service/app/services/document.py`**: Document management service (*contains SQLModel syntax bug on line 46*).
* **`RAG_service/app/api/Users/userRouter.py`**: Complete authentication and user router (`/users/register`, `/login`, `/refresh`, `/logout`, `/me`).
* **`RAG_service/app/api/Users/dependencies.py`**: Dependency providers for `UserService` and `currentUserDep` OAuth2 token validation.
* **`RAG_service/app/api/Documents/documentRouter.py`**: Document CRUD endpoints (*missing auth guards*).
* **`RAG_service/app/api/Documents/dependencies.py`**: Dependency provider for `DocumentService`.
* **`RAG_service/app/llm/client.py`**: Gemini LLM client setup (*contains missing `import os` bug*).
* **`RAG_service/alembic/env.py`**: Async migration script for Alembic.
* **`RAG_service/alembic/versions/5f54e4d624f8_create_initial_tables.py`**: Alembic migration creating the schema and `vector` extension.

### `frontend/` Client
* **`frontend/package.json`**: Package manifest specifying React 19, Vite, and Tailwind CSS v4.
* **`frontend/vite.config.ts`**: Vite build configuration with `@tailwindcss/vite` plugin.
* **`frontend/src/index.css`**: CSS entry point importing Tailwind (`@import "tailwindcss";`).
* **`frontend/src/main.tsx`**: React DOM mounting entry point.
* **`frontend/src/App.tsx`**: Root React component (*placeholder template*).

---

## 13. Identified Bugs & Roadmap to Completion

### Critical Bugs Identified in Existing Code
1. **`RAG_service/app/services/document.py` (Line 46)**:
   ```python
   new_document.sqlmodel_update(data.model_dump(...))
   ```
   *Bug*: `Document` is a SQLAlchemy Base model, not a SQLModel instance. Calling `sqlmodel_update` will raise an `AttributeError` at runtime. Should be updated using standard Python `setattr(new_document, key, value)` dictionary iteration.
2. **`RAG_service/app/llm/client.py` (Line 6)**:
   ```python
   API_KEY = os.getenv("GOOGLE_API_KEY")
   ```
   *Bug*: Missing `import os` statement at the top of the file, causing a `NameError` upon invocation.
3. **Missing Authentication on Document Routes (`app/api/Documents/documentRouter.py`)**:
   *Bug*: The document routes currently do not accept or validate `currentUserDep`, allowing unauthenticated access to document records.

### Development Roadmap to Full Completion

#### Phase 1: Fix Backend Bugs & Complete Core Services
* Fix `sqlmodel_update` in `app/services/document.py`.
* Fix `import os` in `app/llm/client.py`.
* Add `currentUserDep` JWT protection to `documentRouter.py`.
* Implement `POST /documents` with `UploadFile` support for real file persistence.

#### Phase 2: RAG Pipeline & Async Worker Implementation
* Implement `app/pipeline/chuncking.py` (LangChain text splitter integration).
* Implement `app/pipeline/embedding.py` using `sentence-transformers` (`multilingual-e5-small`).
* Implement `app/pipeline/retrieval.py` for pgvector cosine distance queries (`<=>`).
* Create `app/worker.py` using `arq` + `redis` to handle background document indexing (`embed_document`) and stuck document sweeping (`sweep_stuck_documents`).

#### Phase 3: Chat & Message Endpoints
* Implement `app/services/chat.py` and `app/api/Chats/chatRouter.py` (`POST /chats`, `GET /chats`, document attachment).
* Implement `app/services/msg.py` and `app/api/Msgs/msgRouter.py` (`POST /chats/{id}/messages`) to execute vector retrieval, assemble LLM prompts, invoke Gemini API, and record citation source chunks in `msg_chunk`.

#### Phase 4: React Frontend Implementation
* Add theme custom properties (`theme.css`) implementing the Fahemak design system tokens (`--green-200`, `--gold-400`, RTL rules).
* Create API client (`src/api/client.ts`) with automatic JWT memory storage and refresh token retry logic.
* Implement `AuthProvider` and authentication screens (`LoginPage`, `RegisterPage`).
* Build document management UI (`DocumentUploader`, `DocumentList`, status polling hook).
* Build chat interface (`ChatWindow`, `MessageBubble`, `SourceCitation` gold badge).
