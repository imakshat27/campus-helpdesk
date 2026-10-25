# Account sessions and live chat: final verification

Implemented on `codex/account-live-chat`. The login stage was pushed to main before the user changed branch instructions. Subsequent work is on the feature branch; no further main pushes were made.

## Delivered behavior

- Two provisioned role accounts with Argon2 hashes, opaque hashed server sessions, eight-hour HttpOnly cookies, credential-change revocation, rotating logins and immediate logout revocation. Existing staff credentials were preserved; the generated student credential is only in the ignored local backend settings.
- Account-owned saved history, conversation creation/resumption, explicit consent with the original message ID, one active ticket, AI pause during staff takeover, staff acceptance/replies, resolution and explicit student reopening. Legacy anonymous conversations stay unclaimed; historical confirmed tickets remain staff-accessible.
- Ordered, committed message storage and client request IDs. Same-request retries do not duplicate messages. Conversation row locks serialize production writes; uniqueness constraints protect message ordering and active tickets. SQLite write contention returns a recoverable conflict and was exercised through a same-ID retry in the isolated browser check. Production Postgres concurrency has not been load-tested.
- Short-lived, hashed, single-use WebSocket tickets sent in the first frame; exact Origin checks, active session checks before delivery, expiry checks and logout disconnects. Only committed invalidations are sent, only to authorized accounts. HTTP reload restores missed transcript/queue updates after reconnect. One backend worker is required; no shared broker or new paid infrastructure was added.

## Executed checks

| Check | Observed result |
|---|---|
| `backend/.venv/bin/python -m pytest -q backend/tests` | 109 passed |
| Frontend `npm test` | 23 passed |
| Frontend `npm run build` on Node 24 | Passed |
| Alembic migration parity, upgrade/downgrade and seeded legacy backfill | Passed within backend suite |
| Local Chromium, separate student/staff browser contexts | 11 acceptance checks passed; zero page errors |
| Responsive browser checks | 375×812, 768×1024, 1024×900, 1280×720, 1440×1000; no horizontal overflow; send control inside viewport |
| Configured campus-helpdesk Neon migration | Revision 006 applied |
| Neon account provisioning | Exactly one student and one staff row |
| Neon account integration | Both roles passed login, authorized read, logout and rejected reuse after logout |
| Repository visibility | PRIVATE verified before initial push; checked again before final push |

Browser checks include supported citations and Escape dismissal, cancelling a manual handoff, no ticket before consent, live queue arrival after consent, staff acceptance, two-way messages, concurrent student/staff submissions, refresh, offline recovery, resolution/reopening, and logout/new-login history. Evidence and viewport screenshots are in `browser-checks.json` and `screenshots/`.

The browser server uses only a temporary SQLite database, generated temporary test credentials, and explicitly controlled answers. It never contacts Neon or the model. Neon verification used account login/read/logout only; it did not create conversations or tickets or call the model.

## Deployment limits

The feature branch was not deployed to the production hosts. Production Vercel rewriting/cookies and hosted WebSocket connectivity remain unverified. Configure the new student account settings privately on Render before deploying; preserve the existing staff settings. HTTP requests use the same-origin proxy; direct WebSocket connections require the exact frontend Origin and the matching backend URL. See `DEPLOYMENT.md`.

The paid live context/consent regression was not run: it requires separate explicit test confirmation and creates one demo ticket. Existing source-backed retrieval and consent behavior passed the controlled backend regression suite.

VERDICT: PASS
