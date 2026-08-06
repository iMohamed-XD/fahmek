# فاهمك (Fahemak) — Frontend Folder Structure

React + TypeScript, feature-based organization. Maps directly onto the
FastAPI route surface in `routing_logic.md` (`/auth`, `/documents`,
`/chats`) — no server logic lives here, this is a pure REST client.

```
frontend/
├── public/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── documents.ts
│   │   ├── chats.ts
│   │   └── types.ts
│   │
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx
│   │
│   ├── assets/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── icons/
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── context/
│   │   │   ├── hooks/
│   │   │   └── types.ts
│   │   │
│   │   ├── documents/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types.ts
│   │   │
│   │   └── chat/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types.ts
│   │
│   ├── hooks/
│   ├── lib/
│   ├── pages/
│   ├── styles/
│   ├── types/
│   ├── constants/
│   ├── main.tsx
│   └── index.css
│
├── index.html
├── vite.config.ts
├── package.json
└── tsconfig.json
```

---

## 1. `src/api/` — Backend contract layer

The only place that knows FastAPI's route shapes. Every file here maps
1:1 to a router in `routing_logic.md`.

| File | Purpose |
|---|---|
| `client.ts` | A single `fetch`/`axios` instance: base URL, JSON headers, attaches the in-memory JWT access token to every request, and centralizes 401 → refresh-token retry logic. |
| `auth.ts` | `login()`, `register()`, `refresh()` — thin wrappers around `POST /auth/*`. |
| `documents.ts` | `uploadDocument()`, `listDocuments()`, `getDocument()`, `getDocumentStatus()`, `deleteDocument()` — maps to `/documents/*`. |
| `chats.ts` | `createChat()`, `listChats()`, `getChat()`, `sendMessage()`, `listMessages()`, `attachDocument()`, `detachDocument()` — maps to `/chats/*`. |
| `types.ts` | Request/response DTOs mirroring the Pydantic schemas (`DocumentRead`, `MsgRead`, `ChatRead`, etc.) so a backend schema change is a one-file diff on this side. |

**Rule**: components never call `fetch` directly. They call functions from
`api/`. This is what keeps the JWT-attachment and refresh logic in one
place instead of duplicated at every call site.

## 2. `src/app/` — Application shell

| File | Purpose |
|---|---|
| `App.tsx` | Root component — mounts providers and the router. Replaces the current placeholder `App.tsx`. |
| `router.tsx` | Route table (React Router or equivalent): public routes (`/login`, `/register`) vs. protected routes (`/documents`, `/chats/:id`) gated on `AuthContext`. |
| `providers.tsx` | Composes context providers (`AuthProvider`, theme/RTL provider, query client if you add TanStack Query) into one wrapper so `App.tsx` stays flat. |

## 3. `src/assets/`

Static, non-code files — logo, `vite.svg`/`react.svg` (existing), fonts if
self-hosted (relevant for the Reem Kufi/kufic wordmark from the design
system). No logic.

## 4. `src/components/` — Shared, feature-agnostic UI

Anything reused across more than one feature lives here, not inside a
`features/*` folder.

| Subfolder | Purpose |
|---|---|
| `ui/` | Primitive building blocks: `Button`, `Input`, `Card`, `Badge`, `Spinner`, `Modal`. Styled directly off the design-system tokens (`--green-*`, `--gold-*`, `--neutral-*`, `--status-*`) — this is the one place those CSS variables get consumed as component styles, so a token change propagates everywhere instead of being re-implemented per feature. |
| `layout/` | `AppShell`, `Sidebar`, `Header`, `Footer` — the RTL-first page chrome (`dir="rtl"` set once here, not per-page). |
| `icons/` | Thin wrapper components around the chosen icon set (Tabler, per the design system), including the centralized RTL-mirror handling (`transform: scaleX(-1)`) for directional icons — implemented once here per the design system's own recommendation, not per usage. |

## 5. `src/features/` — Domain modules

Each feature folder is self-contained: its own components, hooks, and
types, so a feature can be read, tested, or removed without hunting
through the rest of the tree.

### `features/auth/`
- `context/` — `AuthContext` + `AuthProvider`. Holds the JWT access token
  **in memory only** (per `tech_stack.md` §6 — not `localStorage`, to limit
  XSS exposure), plus `user`, `login()`, `logout()`, and silent-refresh
  wiring on mount.
- `components/` — `LoginForm`, `RegisterForm`.
- `hooks/` — `useAuth()` (consumes the context), `useRequireAuth()` (route
  guard hook used by `router.tsx`).

### `features/documents/`
- `components/` — `DocumentUploader`, `DocumentList`, `DocumentCard`,
  `StatusBadge` (renders `document.status` using the semantic color
  tokens: `--status-neutral/pending/success/danger`).
- `hooks/` — `useDocuments()` (list + upload), `useDocumentStatus(id)`
  (polls `GET /documents/{id}/status` at an interval while status is
  `uploaded`/`chunking`/`embedding`, stops on `indexed`/`failed` —
  encapsulates the poll-and-stop logic described in `routing_logic.md`
  Flow A so no component has to manage its own `setInterval`).
- `types.ts` — `Document`, `DocumentStatus` union type matching the
  backend enum exactly.

### `features/chat/`
- `components/` — `ChatWindow`, `MessageList`, `MessageBubble`,
  `MessageInput`, `SourceCitation` (renders `msg_chunk` results — the
  gold-accent citation badge from the design system).
- `hooks/` — `useChat(chatId)` (loads messages, exposes `sendMessage`),
  `useChatDocuments(chatId)` (attach/detach against `chat_document`).
- `types.ts` — `Chat`, `Message`, `SourceChunk` (`{ chunk_id,
  similarity_score }`, matching the resolved `/query` response-shape
  decision in `routing_logic.md`).

## 6. `src/hooks/` — Cross-feature hooks

Generic hooks with no domain knowledge: `useDebounce`, `useLocalTimer`,
`useMediaQuery`. If a hook imports from `api/documents.ts` or
`api/chats.ts`, it belongs in that feature's `hooks/`, not here.

## 7. `src/lib/`

Framework-agnostic utilities: date formatting, file-size formatting
(bytes → human-readable, relevant for `DocumentCard`), class-name merging
helper (`cn()` for conditional Tailwind classes), error-shape normalizer
for API error responses.

## 8. `src/pages/` — Route-level composition

Thin components that assemble `features/*` components into a full screen
and connect them to route params. No business logic here — a page is a
layout arrangement, not a place to write fetch calls.

Expected pages: `LoginPage`, `RegisterPage`, `DocumentsPage`, `ChatPage`.

## 9. `src/styles/`

Tailwind v4 theme extension. Since Tailwind v4 is CSS-first
(`@theme {}` in `index.css` per `vite.config.ts`'s
`@tailwindcss/vite` plugin), this folder holds the token definitions from
`fahemak_design_system.md` as actual CSS custom properties:

```css
/* styles/theme.css, imported from index.css */
@theme {
  --color-green-50: #F5F9EE;
  --color-green-200: #C0DD97;
  --color-green-800: #27500A;
  --color-gold-400: #EF9F27;
  --color-status-success: #639922;
  --color-status-danger: #C1443A;
  /* ...full ramp from fahemak_design_system.md */
}
```

This is the single source of truth for color tokens — `components/ui/`
consumes these via Tailwind utility classes (`bg-green-800`,
`text-status-danger`), never hardcoded hex values.

## 10. `src/types/` — Shared, cross-feature types

Types with no single feature owner: `ApiError`, `PaginatedResponse<T>`,
`ID` aliases. Feature-specific types (`Document`, `Message`) stay inside
their feature folder, not here — avoids this folder becoming a dumping
ground.

## 11. `src/constants/`

`ROUTES` (path constants for the router, avoids magic strings),
`DOCUMENT_STATUS` (enum mirroring the backend state machine, imported by
both `StatusBadge` and `useDocumentStatus`'s stop condition), API base
URL fallback.

## 12. Root files

| File | Purpose |
|---|---|
| `main.tsx` | Unchanged — mounts `App` into `#root`. |
| `index.css` | Unchanged entry (`@import "tailwindcss";`), plus `@import "./styles/theme.css";` once that file exists. |

---

## Why feature-based over type-based (`components/`, `hooks/`, `pages/`
flat at the top level)

For a 3-feature app (auth, documents, chat) with real cross-cutting
concerns (JWT lifecycle, status polling, citation rendering), colocating
each feature's components/hooks/types keeps related code adjacent and
makes the RAG-specific logic (polling, citations) easy to find and reason
about in isolation — you can open `features/documents/` and see the
entire upload → status → indexed lifecycle without jumping across
directories. `components/`, `hooks/`, `lib/` stay reserved for things with
no single feature owner, which keeps that boundary meaningful instead of
becoming a second home for feature code.

## Not yet decided (flag before scaffolding)

- **Data-fetching library**: plain hooks + `api/` functions above assumes
  manual `useState`/`useEffect`. If you want caching, dedup, and
  background refetch (especially useful for the status-polling hook),
  consider **TanStack Query** — it would live as a `queryClient` added to
  `app/providers.tsx`, with `api/*.ts` functions passed straight in as
  query/mutation functions. Worth deciding before writing
  `useDocumentStatus`, since retrofitting polling logic onto Query later
  means a rewrite, not an addition.
- **Refresh-token storage**: `tech_stack.md` flags this as open — httpOnly
  cookie vs. longer-lived JWT changes what `client.ts`'s refresh call
  looks like (cookie = automatic on request; token = explicit storage
  somewhere more durable than memory, which reopens the XSS question).