# Campus Helpdesk

A campus support prototype with a React chat interface, source-backed RAG answers, a searchable sample knowledge base, and a protected staff queue. Uses FastAPI, OpenRouter, and Neon Postgres with pgvector. The React interface uses shadcn/ui with Radix primitives, Tailwind semantic tokens, and locally bundled Inter. Its paper-and-evergreen theme keeps navigation quiet, labels the question box and send action, and uses editable example questions.

All campus content is **fictional sample information**, not official VIT policy. Event questions use the assignment's reference date, **16 October 2026**, and answers include exact dates.

## Current local setup

The `campus-helpdesk` Neon project is provisioned in Singapore, with database `campus_helpdesk` on branch `main`. pgvector is enabled; migrations are applied; 29 sources and 37 passages are loaded. The local `backend/.env` contains the configured connection and is restricted to owner access. Do not copy it into a submission or commit it.

OpenRouter live answers and the protected staff queue have been verified. See `reports/live-evaluation.md` for the automatic results and `reports/reviewed-evaluation.md` for source-by-source agent review. Project identifiers and future agent instructions are in `.neon/project.json` and `AGENTS.md`. Neon plugin access was used during setup, but its latest status is not installed; install and connect it for direct agent project-management tools. The app's database connection works independently.

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
```

Use the connection string from your Neon console; ordinary `postgresql://` URLs are also accepted. URL-encode special characters in database passwords. Set `OPENROUTER_MODEL` to a model available to your account with JSON mode support. No paid calls happen during installation, seeding, or unit tests.

Apply the initial migration and ingest the approved collection (run from `backend/`):

```sh
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from the project root:

```sh
npm run dev --prefix frontend
```

Open [Campus Helpdesk](http://127.0.0.1:5173). API documentation is at [FastAPI docs](http://127.0.0.1:8000/docs).

If credentials have not been supplied, the interface still opens and the knowledge browser can show the **explicitly labelled bundled sample collection**. Chat reports configuration/service errors; it does not simulate answers or pretend to save tickets. Staff access is disabled until credentials are configured.

## How it works

1. `knowledge/faqs.json` contains 25 approved sample FAQs; `knowledge/documents/` contains four Markdown guides.
2. The seed command splits guides at section headings, generates 384-dimensional embeddings, and stores documents/chunks in Neon. Re-running updates the seed sources without duplicating them.
3. For follow-ups, OpenRouter first rewrites the latest message into a standalone search question using up to 20 recent conversation messages. This works for longer questions, not just short replies. Search retrieves pgvector and keyword candidates and ranks them using semantic similarity plus token overlap. Only approved documents can be retrieved.
4. The backend supplies retrieved passages and recent conversation context to OpenRouter. When the question refers to the previous topic, it also re-reads the last cited passages from the database, checking their approval again before reuse. The model may answer, clarify, or report unsupported information. Facts must come from supplied passages.
5. The backend rejects missing or unknown answer citations and constructs source cards from the retrieved records. Citation validation establishes provenance; it cannot by itself prove that every generated claim is correct. Human review is part of evaluation.
6. Unsupported questions ask whether the student wants a support ticket. No ticket is created at this point. Clicking “Yes, raise a ticket” or affirming the pending offer in chat creates it; “No thanks” declines. Explicit handoff from a supported answer also asks for confirmation. The request identifies the exact question to send, so a later message cannot change the ticket target. Saved references appear only after commit succeeds.
7. Greetings and thanks receive simple conversational replies without knowledge retrieval or ticket creation. Staff authenticate to read confirmed tickets and conversation context, and can mark tickets resolved or reopen them.

Conversations persist in the database; the current browser tab keeps its conversation ID and displayed messages in session storage. New conversation clears that local view. No student account system is included. Conversation UUIDs act as unguessable handles; do not use this prototype for sensitive student records. Staff credentials stay in memory in the UI and are sent only to the backend. Use HTTPS when moving beyond localhost.

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
- UI tests cover failed submissions, retained drafts, cited answers, handoffs, searchable sources, labelled preview data, and failed staff login.

For the actual assignment's end-to-end test table, configure the services, seed the database, start the API, then run from `backend/`:

```sh
uv run python -m app.evaluate
```

This calls the configured OpenRouter model and database, consumes API credits, and creates 12 conversations. The two unsupported cases first verify a ticket offer with no ticket reference, then explicitly simulate affirmative student confirmation in separate requests to test ticket creation. Outputs `reports/live-evaluation.csv`, `.json`, and `.md`. Automated text/source checks are deliberately labelled heuristic; review the cited passages and adjust the correctness judgement in your submitted table. A valid alternative guide citation may need manual approval. Missing credentials or network failures are recorded as errors, never as passes.

The 12 queries are in `knowledge/evaluation.json`. Retrieval tuning should use additional development queries rather than changing expected results to match the system.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Database connectivity and answer configuration status |
| POST | `/api/chat` | `{message, conversation_id?}` → outcome, answer, sources, question ID, optional ticket offer/reference |
| GET | `/api/conversations/{id}` | Stored conversation messages |
| GET | `/api/knowledge?q=&category=` | Approved sources |
| GET | `/api/knowledge/{id}` | Source detail |
| POST | `/api/conversations/{id}/escalate` | Requires `{message_id, confirmed: true}`; send that exact question and reuse an existing open ticket |
| GET | `/api/staff/tickets?status=open` | Protected queue (`open`, `resolved`, or `all`) |
| PATCH | `/api/staff/tickets/{id}` | Protected status change: `{status: "resolved"}` |

## Design and boundaries

Solid cobalt navigation, a white canvas, near-black text and explicit borders, Inter, readable text, responsive navigation, accessible native dialogs, clear focus, and restrained motion. Pastel tiles and soft tinted surfaces have been removed. No gradients or glass effects. Design notes: `design-system/campus-helpdesk/MASTER.md`.

V1 runs locally against Neon. It does not publish a site, send emails, support staff replies/student notifications, or provide institutional SSO. Tickets are routed to the app's staff queue. Public deployment would need HTTPS, proper staff identity/session management, request limits, and a privacy/retention policy appropriate to the institution.
