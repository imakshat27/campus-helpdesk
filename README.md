# Campus Helpdesk

A campus support prototype with a React chat interface, source-backed RAG answers, a searchable official-source knowledge base, and a protected staff queue. Uses FastAPI, OpenRouter, and Neon Postgres with pgvector. The React interface uses shadcn/ui with Radix primitives, Tailwind semantic tokens, and locally bundled Inter. Its paper-and-evergreen theme keeps navigation quiet, labels the question box and send action, and uses editable example questions.

The default corpus is now **public VIT Vellore information downloaded on 24 October 2026**. This is an independent prototype, not an official VIT service. Source dates and academic-year restrictions matter; retrieved pages are not a guarantee of current policy. The original fictional assignment corpus remains available only in explicit sample mode, using the scenario date 16 October 2026.

## Current local setup

The `campus-helpdesk` Neon project is provisioned in Singapore, with database `campus_helpdesk` on branch `main`. pgvector is enabled; migrations are applied; 50 official sources and 1,073 passages are loaded; 968 source-linked extractive Q&A records are also included. The local `backend/.env` contains the configured connection and is restricted to owner access. Do not copy it into a submission or commit it.

OpenRouter live answers and the protected staff queue have been verified. See `reports/official-context-and-consent.md` for the current live follow-up/consent checks and `reports/official-retrieval.md` for vector retrieval coverage. Earlier `live-evaluation.*` and `reviewed-evaluation.*` reports describe the fictional sample corpus. Project identifiers and future agent instructions are in `.neon/project.json` and `AGENTS.md`. Neon plugin access was used during setup, but its latest status is not installed; install and connect it for direct agent project-management tools. The app's database connection works independently.

## Requirements

- Node.js 22.12+ (or a compatible newer release), npm
- Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/)
- A Neon Postgres database with permission to enable the `vector` extension
- An OpenRouter API key and a model supporting JSON-object responses
- Internet on first ingestion to download `sentence-transformers/all-MiniLM-L6-v2`; subsequent runs can use its local cache

## Set up

From the project root:

```sh
npm ci --prefix frontend
cd backend
uv sync --python 3.12
cp .env.example .env
```

Edit `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@YOUR-NEON-HOST/DB?sslmode=require
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=your-chosen-model-slug
STAFF_USERNAME=your-staff-username
STAFF_PASSWORD=your-staff-password
REVIEW_PASSWORD=your-separate-review-password-at-least-16-characters
SESSION_SECRET=your-random-session-signing-secret-at-least-32-characters
```

Use the connection string from your Neon console; ordinary `postgresql://` URLs are also accepted. URL-encode special characters in database passwords. Set `OPENROUTER_MODEL` to a model available to your account with JSON mode support. No paid calls happen during installation, seeding, or unit tests.

Apply migrations and download/process the public collection (run from `backend/`):

```sh
uv run alembic upgrade head
uv run python -m app.import_official
uv run python -m app.build_qna
uv run python -m app.seed
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from the project root:

```sh
npm run dev --prefix frontend
```

Open [Campus Helpdesk](http://127.0.0.1:5173). API documentation is at [FastAPI docs](http://127.0.0.1:8000/docs).

If services are unavailable, the interface reports a load/configuration error. It does not substitute fictional sources, simulate answers, or pretend to save tickets. Staff access requires configured credentials.

## How it works

1. `knowledge/official/manifest.json` indexes public VIT Vellore pages and PDFs; `processed/` contains cleaned text and `qna.json` contains extractive section records. The original sample corpus is kept separately.
2. The seed command splits guides at section headings, generates 384-dimensional embeddings, and stores documents/chunks in Neon. Re-running updates the seed sources without duplicating them.
3. For follow-ups, OpenRouter first rewrites the latest message into a standalone search question using up to 80 stored conversation messages, bounded to recent turns and early topic anchors. This works for longer questions, not just short replies. Search retrieves pgvector and keyword candidates and ranks them using semantic similarity plus token overlap. Only approved documents can be retrieved.
4. The backend supplies retrieved passages and recent conversation context to OpenRouter. When the question refers to the previous topic, it also re-reads the last cited passages from the database, checking their approval again before reuse. The model may answer, clarify, or report unsupported information. Facts must come from supplied passages.
5. The backend rejects missing or unknown answer citations and constructs source cards from the retrieved records. Citation validation establishes provenance; it cannot by itself prove that every generated claim is correct. Human review is part of evaluation.
6. Unsupported questions ask whether the student wants a support ticket. No ticket is created at this point. Clicking “Yes, raise a ticket” or affirming the pending offer in chat creates it; “No thanks” declines. Explicit handoff from a supported answer also asks for confirmation. The request identifies the exact question to send, so a later message cannot change the ticket target. Saved references appear only after commit succeeds.
7. Greetings and thanks receive simple conversational replies without knowledge retrieval or ticket creation. Staff authenticate to read confirmed tickets and conversation context, and can mark tickets resolved or reopen them.

Private review access now requires a separate shared password and an expiring signed session. Chat and conversation endpoints enforce authentication on the backend; conversations are restricted to the session that created them. Global and per-session request budgets persist in Neon and reserve capacity before paid work, including on failed requests. Default global allowance is 100 chat requests per UTC day. These are request caps, not monetary caps; configure an OpenRouter key credit limit too. See [DEPLOYMENT.md](DEPLOYMENT.md) for all settings, session revocation and limitations.

Conversations persist in the database; the current browser tab keeps its signed session, conversation ID and displayed messages in session storage. New conversation clears that local view. No individual student account system is included; do not use this prototype for sensitive student records. Staff credentials stay in memory in the UI and are sent only to the backend. Use HTTPS when moving beyond localhost.

## Validation

From `backend/`:

```sh
uv run pytest -q
uv run python -m app.check_retrieval
# Live check: requires a running API and configured services; confirms one demo ticket.
uv run python -m app.check_conversation
```

From the project root:

```sh
npm test --prefix frontend
npm run build --prefix frontend
```

- `reports/controlled-evaluation.md`: 12 actual API test results with controlled retrieval/generation fixtures and isolated SQLite persistence. Covers eight supported, two ambiguous, and two unsupported queries. **Not a live LLM quality result.**
- `reports/retrieval-check.md`: real local embedding retrieval results, when the embedding check has run. **Not a Neon or LLM integration result.**
- `reports/context-and-consent.md`: nine live turns checking the reported “so how much do i pay?” follow-up, later collection questions, a topic change, decline, and explicit ticket consent. Staff queue counts prove that offers/declines do not create tickets.
- Backend tests additionally cover citation rejection, provider/network errors, database/commit failures, staff authentication, document approval, seeding, follow-ups, and ticket resolution.
- UI tests cover failed submissions, retained drafts, cited answers, handoffs, searchable sources, official source provenance and policy tables, and failed staff login.

For a live test table on the current official corpus, configure the services, seed the database, start the API, then run from `backend/`:

```sh
uv run python -m app.evaluate_official
```

This calls the configured OpenRouter model and database, consumes API credits, and creates test conversations. It tests eight supported, two ambiguous, and two unsupported questions without confirming tickets. Outputs `reports/official-live-evaluation.json` and `.md`. Source-family and outcome checks are not independent factual review. The original `app.evaluate` targets the sample corpus and explicitly confirms two test tickets; use it only after switching to sample mode and reseeding.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Database connectivity and answer configuration status |
| POST | `/api/auth/session` | Review password → expiring signed session; login attempts are limited |
| GET | `/api/auth/session` | Validate the current Bearer session |
| POST | `/api/chat` | `{message, conversation_id?}` → outcome, answer, sources, question ID, optional ticket offer/reference |
| GET | `/api/conversations/{id}` | Stored conversation messages |
| GET | `/api/knowledge?q=&category=` | Approved sources |
| GET | `/api/knowledge/{id}` | Source detail |
| POST | `/api/conversations/{id}/escalate` | Requires `{message_id, confirmed: true}`; send that exact question and reuse an existing open ticket |
| GET | `/api/staff/tickets?status=open` | Protected queue (`open`, `resolved`, or `all`) |
| PATCH | `/api/staff/tickets/{id}` | Protected status change: `{status: "resolved"}` |

Chat, conversation retrieval and escalation require `Authorization: Bearer <session>`.
The live regression scripts authenticate from local backend settings automatically.
Allow time between runs to respect the configured request limits; do not bypass
the production limits for evaluation.

## Design and boundaries

Warm paper surfaces, evergreen actions, Inter, readable text, responsive navigation, accessible shadcn/Radix dialogs, clear focus, and restrained motion. Original-source links and retrieval dates accompany official source inspection. No gradients or glass effects. Design notes: `design-system/campus-helpdesk/MASTER.md`.

Vercel frontend and Render backend deployment configuration is included; see [DEPLOYMENT.md](DEPLOYMENT.md) for account setup, environment configuration, validation and deployment status. Tickets are routed to the app's staff queue. The prototype does not send emails, support staff replies/student notifications, or provide institutional SSO. Institutional use would need proper staff identity/session management, request limits, and a privacy/retention policy appropriate to the institution.

## Official dataset and refresh

The source manifest and extracted documents are under `knowledge/official/`; the README there documents provenance, OCR and exclusions. Downloaded original files are cached locally in `knowledge/official/raw/` and excluded from Git. The processed corpus and Q&A extracts are versioned. To refresh, run `uv run python -m app.import_official --refresh`, `uv run python -m app.build_qna`, then `uv run python -m app.seed` from `backend/`. This is a manual refresh, not a scheduled monitor.

`KNOWLEDGE_MODE=official` is the default. Seeding disables the prior corpus so sample fees and hours cannot leak into official answers. For the assignment's original demo, explicitly set `KNOWLEDGE_MODE=sample` and reseed; its old evaluation scripts target that sample data. The current live regression command, `uv run python -m app.check_conversation`, selects the appropriate corpus test and confirms one test ticket. `uv run python -m app.check_official` measures top-eight source-family recall over 30 questions without generating model answers.

Conversation resolution now uses up to 80 stored messages and a bounded context of recent turns plus early topic anchors. Source documents remain the factual authority; conversation history is never treated as an approved source. Returning to earlier topics is tested. This is bounded conversational context, not unlimited memory or access to other chats.

Public coverage does not include private attendance, timetable/room allocations, live seats, personal records, passwords or registration state. Missing facts still ask before raising a staff ticket. An independent staff/source review and current university confirmation remain necessary for critical or changing policy details.


Current verification: 71 isolated backend tests, 15 frontend tests, production build, 30 source-family retrieval checks, 12 live outcome/source checks and eight live context/consent turns. See `reports/official-dataset.md` for limits and earlier failed runs. Browser review of the new UI changes is pending because local browser use was disabled in Work settings during this revision.
