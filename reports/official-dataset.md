# Official VIT Vellore expansion — 24 October 2026

## Scope and corpus

- 50 public VIT sources, 1,073 active searchable passages in Neon pgvector, and 968 extractive Q&A records. The original 29 fictional documents remain in the database but are not approved/active.
- Public HTML, PDF text and OCR of the scanned library policy. Original downloads are cached locally; processed Markdown, Q&A and the source manifest are versioned.
- Every active document has its original VIT URL, Vellore campus scope, and retrieval timestamp. The manifest includes original-file SHA-256 hashes, source format, and exclusions.
- Q&A records contain section/page discovery questions and exact source extracts, not 968 independently reviewed natural-language FAQs.
- Campus scope is Vellore, explicitly selected by the user. Programme, fee category and document-year applicability must be preserved; public pages do not provide personal VTOP data.

## Coverage

| Category | Documents |
|---|---|
| academics | 3 |
| accessibility | 1 |
| admissions | 4 |
| alumni | 3 |
| careers | 2 |
| events | 1 |
| facilities | 4 |
| hostels | 7 |
| international | 2 |
| library | 2 |
| procedures | 6 |
| research | 3 |
| safety | 3 |
| welfare | 9 |

## Exclusions and limits

The importer follows only allowlisted public VIT URLs, checks robots.txt, and excludes login/portal paths. Missing pages, unreadable content and low-content pages are recorded; it does not silently fabricate a document. OCR output must be checked against the original PDF for critical decisions. Retrieval date is not a publication date or assurance of current policy.

No public-only corpus can guarantee every answer: private attendance, personal schedules and allocations, unpublished lab timings, live availability, passwords and account balances remain unavailable. The old sample ₹200 ID-replacement fee is not a verified official fee and is no longer an active source. The official Students Records Section description covers duplicate ID cards; any fee not published in the imported material requires staff confirmation.

## Processing and retrieval

- Heading/page-aware splitting, bounded passages (~180 words), repeated heading context, and normalization of repeated site boilerplate. Tables stay in extracted HTML Markdown; PDFs retain page numbers.
- Hybrid Sentence Transformers + pgvector retrieval with keyword candidates ranked by term matches, plural normalization, and narrow domain synonyms (for example day scholar → hostel/residential). Synonyms add search terms, not invented policy facts.
- Return up to eight distinct passages with a maximum of three from any one document. Retrieval avoids loading full long documents for every candidate.
- Source IDs remain strictly validated. Invalid model citations get one bounded repair attempt; an invalid answer is never silently assigned a guessed citation.

## Conversation and UX

- Read up to 80 actual stored messages; bound model input to recent 48 messages plus up to eight early anchors within 48,000 characters. The latest turns get budget priority. This is bounded memory, not unlimited history or cross-chat access.
- Resolve follow-ups into standalone retrieval questions; resolve a return to an earlier topic using conversation text. Independent topic searches lead the context, followed by revalidated earlier citations.
- Updated home examples to official topics; original VIT link and retrieval dates in source dialogs; readable Markdown lists/tables; deduplicated source buttons while retaining all cited passages.
- Category filters use actual source categories, multiword search matches terms, and long result sets load 15 at a time. Unsent drafts survive navigation and clear on a new conversation.
- Removed the bundled fictional-knowledge fallback during official API outages and separated old sample chat storage. Markdown rendering is loaded only when source detail is opened.

## Verification

- 71 backend tests and 15 frontend tests passed; production TypeScript/Vite build passed.
- Applied Alembic revision 002 to the configured Neon project. Actual approved-source count and active passage counts were checked directly; no approved source lacks a URL.
- Real retrieval coverage and live answer results are in `official-retrieval.*` and `official-live-evaluation.*`. Retrieval recall is distinct from factual answer accuracy.
- Live context/consent results are in `official-context-and-consent.*`. Only the explicit test confirmation saves a ticket.
- Fresh browser verification/screenshots could not run: local browser use is disabled in Work settings. Component tests cover original-source links, policy tables, dialogs, mobile Sheet focus, search, retained drafts and ticket consent, but visual reflow/200% zoom still needs a browser review.

## Rebuild

From `backend/`:

```sh
uv run alembic upgrade head
uv run python -m app.import_official --refresh
uv run python -m app.build_qna
uv run python -m app.seed
uv run python -m app.check_official
uv run python -m app.evaluate_official
uv run python -m app.check_conversation
```

The last command confirms one demo ticket. The live evaluator creates conversations without confirming tickets. The importer is an on-demand refresh; no monitor or schedule was installed.


## Live test iterations

The first 12-query live run passed 11 automatic checks and failed a broad hostel-fee question with HTTP 502. A scoped fee clarification guard now asks for hostel, occupancy/AC preference, student category and academic year. A later run passed those clarification checks but hit a transient provider/output failure on the day-scholar query. These failed runs are retained in `official-live-initial.json` and `official-live-before-retry.json`. The provider layer now retries transient transport/HTTP failures and invalid structured output at most once within a split time budget, while permanent authentication failures are not retried. Credentials and raw prompts/responses are not logged. Bounded citation repair and strict validation remain in place. The current `official-live-evaluation.*` records the final run, including any remaining failures rather than overwriting them as passes.


## Final results

- 30/30 expected source families retrieved in the final 50-document corpus. This is top-eight source-family recall, not a claim of 100% answer accuracy or universal coverage.
- 12/12 live automatic outcome/source-family checks passed: eight supported, two clarifications, two missing/private facts. The evaluator saved no tickets and verified unchanged staff queue counts.
- The final eight-turn live context/consent rerun passed on the final corpus: a hostel follow-up, independent library topic, explicit return to hostel booking, missing facts, decline and explicit confirmation. Exactly one ticket was saved in that regression run after affirmative consent.
- Prior failures are preserved as described above. Responses remain model-generated; a human review is still needed before treating the collection as institutionally approved.
- Queue context now uses two bounded SQL queries for a non-empty ticket list rather than one query per ticket; a regression test verifies batching and preserved conversation context.


An additional ID-fee check confirmed that the fictional ₹200 fee was not returned from official sources. Its first official response named the Students’ Records Section without a fee; this did not answer the exact requested price. The generation policy was tightened to treat that as unsupported and offer confirmation rather than substituting a related-office answer. The follow-up check is saved in `official-id-fee-check.json`.

For exact price questions, a related-office answer without an actual monetary value (or an explicit no-charge statement) is now classified as missing information. Phone numbers and “feel free to contact” are not prices. This keeps a contact-only answer from hiding the unavailable fee and offers staff routing only with consent. This guard does not independently prove that every quoted amount is correct; source review remains necessary.

The final live exact replacement-ID-fee check returned `needs_staff_confirmation`, explicitly stated no answer was found, and saved no ticket. The fictional sample fee was not reused.
