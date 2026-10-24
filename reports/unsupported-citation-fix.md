# Unsupported answer with a related citation

On 25 October 2026, the hosted `id card cost?` request returned HTTP 502 with
“The answer service returned an inconsistent response.” The same question was
reproduced locally against the configured OpenRouter model and official Neon
corpus. Both initial and repair responses explicitly used `unsupported` but
included one valid retrieved passage ID. Neither response established a fee.

The validator now removes redundant valid citations from an explicitly
unsupported result and replaces its generated message with a fixed internal
message. The API displays its existing fixed ticket-consent question, never the
unsupported model text. Unknown citations remain errors for every outcome;
answers without citations and clarification responses with citations remain
subject to the existing bounded repair and validation rules.

Validation:

- 77 isolated backend tests passed, including the reproduced provider shape,
  no unconfirmed ticket, no provider prose in persisted/displayed replies,
  and continued rejection of unknown IDs for every outcome.
- A live local API request with the configured OpenRouter model and Neon returned
  HTTP 200, `needs_staff_confirmation`, no sources, no ticket reference and a
  message-specific ticket offer. Ticket count before and after was unchanged.
- `uv run python -m app.check_conversation` passed all eight live official-corpus
  context and consent turns. It created exactly one demo ticket after explicit
  confirmation, as documented by that regression command.
- Hosted verification remains pending deployment of the fix.

This does not establish the ID-card fee. Missing official facts must still ask
before routing a question to staff.
