# Citation validation repair — 24 October 2026

The reported query, “how much for a new id card?”, reproduced HTTP 502 with “The answer service returned an invalid citation.” before the fix.

The provider previously received both passage `id` and parent `document_id`, although only the passage ID was citable. The exact invalid provider output was not retained, so a document-ID mixup is a failure mode rather than a confirmed diagnosis of that individual response.

The model now receives only passage IDs, titles, headings and approved content. Instructions require exact passage IDs from the current retrieval set. An invalid or inconsistent citation response triggers one fresh generation using the same evidence and an explicit ID allowlist. Both attempts undergo strict validation. A second invalid response still returns 502 and saves no answer, conversation or ticket. Transport failures are not retried as citation errors. No guessed citations are silently attached.

## Verification

- 55 isolated backend tests passed. New coverage includes document IDs, titles, invented IDs, absent citations, bounded retries, valid responses requiring no retry, provider failures, and API persistence/no-ticket behavior.
- After the fix, the exact query returned HTTP 200 with the ₹200 replacement fee and valid citations: `student-services:1` (Student services handbook) and `faq-14:0` (Replacing a lost student ID). No ticket was created.
- Raw non-secret result summary: `citation-repair.json`.
- Provider generation remains nondeterministic: this adds bounded recovery, not a guarantee that every provider response is valid.

One live regression attempt returned HTTP 502 on the ID collection follow-up. Repeating that exact follow-up in the same conversation succeeded with the Student Support Office collection instructions. This transient failure is retained here rather than treating a single successful fee response as complete service reliability. The full nine-turn check was rerun separately.

The complete rerun passed all nine live turns against OpenRouter and Neon, including the fee follow-up, collection, collection timing, independent library question, ticket offer/decline, and explicit consent. Queue counts stayed unchanged until the explicit “yes please”; exactly one confirmed demo ticket was saved. Updated evidence is in `context-and-consent.md` and `context-and-consent.json`.
