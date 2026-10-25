# Vercel frontend, Render backend, Neon database

The checked-in frontend proxy targets `https://campus-helpdesk-1-0oa0.onrender.com`.
The frontend is `https://campus-helpdesk-rho.vercel.app`. These are deployment
configuration values, not proof the latest commit is running on either host.

## Account setup

Set `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `STUDENT_USERNAME`,
`STUDENT_PASSWORD`, `STAFF_USERNAME`, and `STAFF_PASSWORD` privately on Render.
Use different account usernames and passwords of at least 16 characters (8–1024 accepted to preserve existing credentials). Never use
`VITE_` variables for credentials. The previous review password and signing
secret are no longer used; old Bearer tokens and staff Basic auth are rejected.

Set `CORS_ORIGINS` to the exact frontend origins as a JSON array, including
`https://campus-helpdesk-rho.vercel.app` and any explicitly approved preview or
custom domains. Every state-changing HTTP request must carry an allowed Origin.
Command-line clients must set it explicitly too.

Startup runs Alembic migrations and `python -m app.provision_accounts` before
serving. Provisioning keeps existing account IDs and password hashes when
credentials are unchanged; changing credentials revokes that account's sessions.
Do not set weak placeholder credentials to make startup pass.

Production uses `COOKIE_SECURE=true`. The opaque HttpOnly, SameSite=Lax cookie
is scoped to `/api` with an eight-hour expiry. Only its SHA-256 hash is stored in
Neon. Logout deletes the server session. HTTP requests always use `/api` on the
frontend origin; Vercel rewrites that prefix to Render before its SPA fallback.
No third-party cookie access is required. When moving the backend, update the
rewrite destination as well.

Locally, set `COOKIE_SECURE=false` in the gitignored `backend/.env`, set both
accounts, then run from `backend/`:

```sh
uv sync
uv run alembic upgrade head
uv run python -m app.provision_accounts
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend with `npm ci` and `npm run dev` from `frontend/`. Its proxy
forwards `/api` to port 8000. Use a supported Node version (22.12+ or 24).

## Persistence and limits

Use only the campus-helpdesk Neon project and branch recorded in
`.neon/project.json`. Migrations preserve legacy conversations without claiming
them for the new student account. Existing confirmed tickets remain staff-only.

`CHAT_ENABLED=false` pauses AI work. Global and account request limits persist
in Neon, including failures, and re-login cannot reset account allowances.
Defaults: 10 global requests/minute, 100/day; 5 per account/minute, 30/day.
Login limits are 5 per client address/minute and 30 globally/minute. Set a
provider-side credit limit separately. No paid infrastructure changes are needed.

## Deployment verification

Deploy both hosts together: the API authentication contract has changed.
Verify login and role redirects, refresh, logout/revocation, forbidden routes,
source-backed answers, and browser cookies through the Vercel proxy. Record
hosted results separately from local test results. A health check alone does
not verify browser integration. Live model/consent regression requires explicit
test confirmation because it saves a demo ticket.

## Saved conversations and staff handoff

Migration 005 backfills deterministic message order and conversation states,
adds sender identities and retry records, and enforces one open ticket per
conversation. Historical duplicate open tickets are preserved as resolved
records; the newest remains active. Historical anonymous owners are retained.
New student history is attached to the student account, not its login sessions.

New conversation creation accepts a client-generated UUID. Message submission
requires a client request UUID; retrying the same request returns the original
result without saving another message. Reusing that UUID for different content
or another conversation is rejected. Staff cannot reply until accepting a
confirmed handoff. Resolving/reopening updates ticket and conversation together.

## Real-time connections

Set `VITE_WS_URL=wss://campus-helpdesk-1-0oa0.onrender.com/api/events` on Vercel
(or use the matching built-in default). For a different backend, change both
this public URL and the HTTP rewrite. Locally the default is
`ws://<frontend-host>:8000/api/events`. No secret belongs in this URL.

The browser obtains a single-use 30-second ticket through the authenticated
same-origin `/api/auth/ws-ticket` endpoint, then sends it in the first WebSocket
frame directly to Render. Query strings never contain authentication tokens.
Only approved frontend Origins can connect. Tickets are stored hashed in Neon.
Sessions are checked on notification delivery and at least every five seconds;
logout closes existing sockets immediately. Each session allows five concurrent
connections. The connection sends only committed-change notifications; clients
reload authorized HTTP state on each change and after reconnecting.

Keep **one Uvicorn worker**. The connection registry is process-local; messages,
statuses and retry records are durable in Neon. Multiple workers or instances
need a shared event broker first. No Redis or paid service is introduced here.
The supplied startup command limits WebSocket frame size to 1024 bytes.

The interface reconnects with increasing delays up to 30 seconds and detects
missing heartbeats. Failed sends retain drafts and their request IDs for retry.
Resolved conversations reject replies; staff takeover never invokes AI. Render
service sleep/restarts can disconnect clients; show reconnection state rather
than promising staff availability or silently simulating successful sends.

## Verification evidence

See `reports/implementation/live-chat.md` and `browser-checks.json`. The browser
acceptance runner is `frontend/scripts/check-chat-browser.cjs`; run it against
`backend/tests/browser_server.py` with a private temporary credential JSON file
and isolated temporary SQLite database. It requires Playwright; a bundled
installation can be supplied through `CAMPUS_PLAYWRIGHT_MODULE`, with
`BROWSER_EXECUTABLE` when needed. Never point this fixture at Neon.

Local browser success does not verify production Vercel rewriting or hosted
WebSocket connectivity. Deploy the feature branch only when its four private
account settings and exact frontend Origin are configured on the backend.
