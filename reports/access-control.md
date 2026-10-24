# Private review access and request budgets

Implemented 25 October 2026. Hosted rollout remains unverified until Render
deploys the access-control commit and receives its new server-only settings.

- Password-gated, eight-hour signed review sessions; frontend login uses existing
  shadcn controls, readable labels, in-place errors and pending feedback.
- Backend authentication on chat, conversation retrieval and escalation, plus
  session ownership. Existing unowned conversations remain unavailable to newly
  authenticated reviewers; authorized staff can still inspect ticket context.
- Persistent atomic global and session request counters in Neon, reserved before
  retrieval/model work and committed independently of failed chat transactions.
- A server-side chat pause switch and fail-closed behavior for missing access
  configuration or unavailable budget storage. Login attempts are also limited.
- No provider credential or shared review password is added to the frontend.

Validation: 92 isolated backend tests and 23 frontend tests passed; production
frontend build passed. Migration 003 was applied to the configured Neon project
through Alembic. A live Neon test with eight concurrent reservations and a limit
of three allowed exactly three, rejected five with 429, then removed its isolated
test counter. Tests cover unauthorized access before retrieval, bad passwords,
tampering, expiry, signing-key rotation, login limits, cross-session access,
legacy ownership, global/session minute/day caps, limits across new logins,
provider errors consuming budget, persistence and budget-database failure.

The authenticated live official context/consent regression passed eight turns,
creating exactly one demo ticket after explicit confirmation. Its local test
server used 30/minute allowances so the regression could finish in one run;
production defaults remain 5/minute per session and 10/minute globally.

Browser visual checks remain pending because computer browser access was disabled
in Work settings. This is shared prototype access, not university SSO. A copied
session remains valid until expiry or signing-secret rotation. Request limits
do not provide an exact dollar cap; use OpenRouter key credit limits as well.
