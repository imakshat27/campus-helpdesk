# Account login stage

Replaced the review password and staff Basic authentication with database-backed student/staff accounts and revocable opaque cookie sessions. Passwords use Argon2; the setup command never prints credentials. HTTP browser calls now use the same-origin API proxy. Mutations require an allowlisted Origin.

Provision locally with `COOKIE_SECURE=false`, both account usernames and passwords (at least 16 characters), then `uv run alembic upgrade head` and `uv run python -m app.provision_accounts`. Production startup runs both commands, requires the four account settings, and uses secure cookies. Existing sessions are revoked when provisioned credentials change. Legacy review tokens are no longer accepted.

Frontend validation: 20 tests passed and production build passed. Backend validation: 94 tests passed initially; the remaining queue query-count assertion was updated for the two authentication lookups and its targeted rerun passed. Migration, authentication, revocation, cookie, role and provisioning tests passed. Repository visibility verified PRIVATE.
