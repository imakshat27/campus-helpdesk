# Saved conversations and staff takeover

Added account-owned history, server-loaded transcripts, deterministic message sequence numbers, request deduplication, and AI/waiting/staff-active/resolved conversation states. Confirmed handoffs persist the exact originating question, enforce one open ticket, and pause AI. Staff must accept before replying; resolution closes replies and explicit reopening returns to the queue. Existing anonymous chats are never claimed by the student account.

Validation: 100 isolated backend tests passed, including migration parity and upgrade/downgrade, history authorization, distinct conversation context, duplicate message requests, mismatched request IDs, repeated handoffs, staff takeover/replies, resolution/reopening and legacy access. 18 frontend tests passed; production build passed. Tests use controlled retrieval/generation and isolated SQLite, not paid model calls. Production Postgres concurrency and hosted browser behavior are not established by these tests.

Live context/consent regression was not run because it requires separate explicit test confirmation and saves a demo ticket.
