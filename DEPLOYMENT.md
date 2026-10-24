# Vercel frontend and Render backend

Deployment URLs:

- Frontend: https://campus-helpdesk-rho.vercel.app
- Backend: https://campus-helpdesk-ye2a.onrender.com

The backend health endpoint has returned HTTP 200 with Neon connected, answer
service configured, official corpus active and campus Vellore. Unauthenticated
staff requests returned 401. Frontend routes return HTML successfully. These
checks alone do not establish successful model answers or browser integration.
The initial frontend build lacked its API URL and initial backend CORS rejected
the frontend origin; the user subsequently reached the chat API from the UI.
The unsupported-response fix described in `reports/unsupported-citation-fix.md`
still requires verification on the hosted service after redeployment.

Local preparation checks passed: 77 backend tests, 18 frontend tests, production
frontend build, migration/startup command against Neon, health/configuration,
50 approved knowledge documents, CORS including staff preflight, rejection of
unapproved origins, and unauthenticated staff denial. Browser and hosted checks
remain pending; local browser automation is disabled in Work settings.

## Render

Connect `imakshat27/campus-helpdesk` to Render through GitHub. Keep the repository
private. Create a Blueprint from the repository's `render.yaml` on `main`.
It defines a Docker web service in Singapore, using the free instance to start.
No additional database is created: the app continues using its existing Neon
`campus_helpdesk` database.

Supply these values in Render's environment settings from the existing local
`backend/.env`, without committing or posting them in chat:

- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `STAFF_USERNAME`
- `STAFF_PASSWORD`
- `REVIEW_PASSWORD`: a separate random review-access password, at least 16
  characters. Share only with intended reviewers; never reuse the staff password.
- `SESSION_SECRET`: a random signing secret, at least 32 characters. Keep it
  server-only. A Blueprint can generate it; manually created services must set it.
- `CORS_ORIGINS`: a JSON array containing the exact production frontend origin,
  for example `["https://your-project.vercel.app"]`. Do not include a trailing
  slash or use a wildcard. Add another origin explicitly if a custom domain is used.

## Private review access and cost controls

Deploy the access-control commit to **both** hosts. Chat, conversation retrieval
and ticket escalation require an expiring signed Bearer session issued after the
review password is checked by Render. The frontend only stores that session in
tab storage; neither password nor OpenRouter key is bundled into frontend code.
Staff queue access additionally requires its separate existing staff credentials.
Public health and approved knowledge endpoints remain available without model
calls. CORS alone does not authenticate requests.

Missing or short `REVIEW_PASSWORD` / `SESSION_SECRET` values close chat access with
503. The existing hosted version remains unprotected until the new backend is
deployed. Suspend the service in Render for immediate containment while setting
up deployment access. `CHAT_ENABLED=false` is the backend kill switch after this
version is deployed. It does not stop requests already running.

Default request budgets use fixed UTC windows in Neon, reserved atomically before
any retrieval or provider request. Limits survive service restarts, new sessions
and provider failures:

| Environment variable | Default |
|---|---:|
| `CHAT_REQUESTS_PER_MINUTE` | 10 globally |
| `CHAT_REQUESTS_PER_DAY` | 100 globally |
| `SESSION_REQUESTS_PER_MINUTE` | 5 per session |
| `SESSION_REQUESTS_PER_DAY` | 30 per session |

Login is limited to five attempts per server-observed client address per minute
and 30 per minute globally. No client-supplied forwarding header is read by the
limiter. These limits can affect multiple people behind one proxy. Limits return
429 with `Retry-After`; budget database failures close access rather than bypassing
limits. Fixed windows can allow a burst across a boundary. One chat request can
make multiple bounded model calls; request budgets are **not dollar spend caps**.
Set a credit limit on the app's dedicated key in
[OpenRouter API keys](https://openrouter.ai/settings/keys), and check usage there.

Sessions expire after eight hours by default. Signing out removes the token from
the tab; a previously copied token stays valid until expiry. Rotate `SESSION_SECRET`
to invalidate all sessions, including after changing the review password.
Changing the password alone does not revoke issued tokens. Conversations belong
to the session that created them; old unowned conversations cannot be claimed by
a new reviewer. The protected staff queue retains its authorized context access.
New login starts a new conversation while preserving an unsent draft.

This is a shared-password gate for private prototype review, not student identity,
institutional SSO or a public multi-user account system. No hosted protection is
confirmed until unauthenticated `/api/chat` requests return 401 (or 503 when
configuration is intentionally missing).

The backend build installs the locked CPU dependencies and downloads
`sentence-transformers/all-MiniLM-L6-v2` into the image. It does not ingest sources
or call OpenRouter. Startup applies Alembic migrations, verifies the 384-dimensional
model, then serves one Uvicorn worker on Render's `PORT`. Database conversations,
sources, vectors and tickets survive service restarts in Neon.

The default model is baked into the image. Changing `EMBEDDING_MODEL` requires
changing the Docker build and re-embedding the corpus; do not change only the
runtime environment variable.

The Docker build remains unverified until a Docker engine or Render build is
available. Local macOS embedding preflight measured about 481 MiB peak RSS;
that is **not** a Linux/Render memory measurement. Validate actual Render memory
under chat traffic before relying on the free instance. No paid upgrade is
authorized by this configuration. Render's free tier sleeps after 15 idle
minutes and can take about a minute to wake; see
[Render's free service limits](https://render.com/docs/free).

## Vercel

Import the same private repository, setting **Root Directory** to `frontend`.
Use the Vite framework preset, Node.js 22.x, `npm ci`, `npm run build` and output
directory `dist`. `frontend/vercel.json` includes SPA navigation rewrites and
response security headers.

Set the public build variable `VITE_API_BASE_URL` to the actual Render service
URL **including `/api`**, such as
`https://your-service.onrender.com/api`. Set it for production and any preview
environment that should connect to the backend. Rebuild after changing it.
Never add the database URL, staff password or provider key to Vercel or any
`VITE_` variable.

After Vercel assigns the frontend domain, add its exact HTTPS origin to Render's
`CORS_ORIGINS` and redeploy the backend. Preview URLs require an explicit CORS
origin; broad preview-domain wildcard access is not enabled.

## Verify before sharing

1. Render `/api/health` returns HTTP 200, `database: connected`,
   `answer_service_configured: true`, and `knowledge_mode: official`.
2. Open the Vercel site and refresh `/knowledge` and `/staff` directly.
3. Verify browser requests reach the actual Render URL and CORS allows the
   production origin, including preflights with `Authorization`.
4. Ask an official-source question, inspect its citation, then ask a follow-up.
5. Ask an unsupported question: an offer should appear with no saved ticket.
   Confirm a ticket only as an explicit demo test, then verify staff access.
6. Confirm unauthenticated chat and staff requests return 401 and failed requests preserve
   the user's draft. Test the first request after a free-instance idle period.

Do not report the app as hosted until both actual deployment URLs and these
checks have been recorded. This remains an independent campus helpdesk prototype;
it has no university SSO, student account system, email delivery or staff replies.
