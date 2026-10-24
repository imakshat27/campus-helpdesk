# Verification — 24 October 2026

## Executed

| Check | Result | Boundaries |
|---|---|---|
| Backend pytest | 43 passed | Isolated SQLite database; controlled provider/retrieval fixtures where appropriate |
| Frontend Vitest | 11 passed | Network failure/draft retention, cited answers, persisted handoff display, source search/filtering, preview labelling, staff login failure, conversation restoration/reset |
| Neural retrieval evaluation | 12/12 passed | Real all-MiniLM-L6-v2 embeddings, production ranking, isolated SQLite cosine calculation; no LLM calls |
| Frontend production build | Passed | TypeScript and Vite |
| npm dependency audit | 0 vulnerabilities | Checked after upgrading Vitest |
| Responsive chat | Passed at 375, 768, 1024, 1440px | No document horizontal overflow; 18px composer text |
| Rendered chat text contrast | Passed | Automated computation over visible text nodes: all at least 4.5:1 against their rendered solid backgrounds |
| Source inspection | Passed in browser | Opens exact source content, native modal focuses close button, Escape dismisses and returns focus to the source row |
| Mobile navigation | Passed in browser | Drawer opens, focus moves to close button; Escape dismisses and restores focus to menu trigger; background made inert |
| Knowledge browser | Passed in browser | All 29 sources available in explicitly labelled offline preview; search narrows results; source detail opens |
| Service configuration failure | Passed against running API | `/api/health` returns 503 with a clear database-configuration message, rather than claiming readiness |

## Reports

- `controlled-evaluation.md` contains the 12 API evaluation cases: eight supported, two ambiguous, two unsupported. These use controlled retrieval and generation and test actual API orchestration/persistence. They are not live model quality measurements.
- `retrieval-check.md` contains the real neural retrieval evaluation. It tests source recall and abstention, not generated-answer correctness.
- `screenshots/chat-desktop.png` and `screenshots/chat-mobile.png` show the reviewed interface.

## Live integration — completed after configuration

- Created Neon project `campus-helpdesk` in Singapore, branch `main`, database `campus_helpdesk`.
- Verified PostgreSQL 18.6 and pgvector 0.8.6; applied Alembic revision `001`.
- Seeded 29 approved documents/FAQs and 37 passages, then executed real pgvector retrieval. The top source for SJT 301 was correct.
- Verified `/api/health` reports a connected database and configured answer service.
- Ran all 12 live queries against OpenRouter (`google/gemini-2.5-flash-lite`) and Neon. The first run exposed an unnamed-event guess; added a server clarification guard and regression tests before the final run.
- The revised live run passes 12/12 automatic checks and agent source review. The evaluator normalizes equivalent date/range formatting and tests explicit consent as a separate request. The original pre-consent results have been superseded by the latest `live-evaluation.*` and `reviewed-evaluation.*` artifacts.
- Verified both final fallback ticket references in Neon, and authenticated queue access. Unauthenticated queue access returns 401.
- Verified a real lab clarification followed by “Robotics” returns the supported answer, and staff resolve/reopen actions both persist in Neon.
- Browser submitted SJT 301 through the UI and displayed the real generated answer with source cards. Screenshot: `screenshots/live-answer.png`.
- Saved non-secret project identifiers in `.neon/project.json` and future agent instructions in `AGENTS.md`. The Neon plugin worked during provisioning but later reported as not installed; future plugin tools require installing and connecting the plugin. Local database access works independently.

## Context, consent and visual revision

- Fixed the exact reported six-word follow-up by replacing the five-word heuristic with standalone query rewriting from recent history. Prior cited chunks are re-read and must still be approved before reuse. New independent topics do not inherit unrelated citations.
- Missing retrieval or unsupported generation now offers a ticket, with no database ticket write. Typed affirmative consent and explicit button confirmation create a ticket for the original question. Declining, greetings, and thanks never create tickets.
- The explicit endpoint requires the question's message ID and `confirmed: true`; an offer alone, a missing body or false confirmation cannot create a ticket. Consent is persisted in conversation context and repeated submissions reuse an existing open ticket.
- The live nine-turn check (`context-and-consent.md`) verifies the original fee question, collection follow-ups, a new library topic, a declined ticket, and a separately confirmed ticket. Queue counts stay unchanged until consent.
- Browser verified the inline “Yes, raise a ticket” / “No thanks” prompt and a successful decline. New screenshots: `screenshots/redesigned-desktop.png`, `screenshots/redesigned-mobile.png`, `screenshots/ticket-consent.png`.
- Replaced pastel surfaces with solid cobalt navigation, white backgrounds, black text/control borders and one blue icon treatment. The mobile top bar is solid blue. All four tested widths (375/768/1024/1440px) have no horizontal overflow. The composer uses 18px text; visible rendered home text passes 4.5:1 contrast. At 1280×720 the full composer fits, with its bottom at approximately 628px.

## Remaining manual checks

- **200% browser zoom:** the available embedded browser did not expose or apply browser zoom controls. Narrow-width reflow was checked, but that is not recorded as a completed 200% zoom test. Manually set 200% browser zoom and confirm navigation, composer, dialogs, and text remain operable without horizontal scrolling.
- **Reduced motion:** CSS includes `prefers-reduced-motion` overrides; media emulation was unavailable, so the preference has not been exercised in a browser.

No email or messages were sent to external staff. Unit tests use disposable SQLite databases. Live evaluation created real demo conversations and tickets in the new Neon project; the application routes handoffs to that protected staff queue.

## shadcn/ui revision — 24 October 2026

- Installed the official shadcn components with CLI 4.22.1 and committed the editable component sources/configuration. Buttons, inputs, textarea, labels, cards, badges, alerts, sidebar/mobile sheet, dialogs, category ToggleGroup, staff Tabs and separators now use these components.
- Retained solid cobalt/white, replaced heavy black outlines with neutral borders, centered the home heading, put the composer ahead of the four compact topic cards, and removed redundant breadcrumb decoration. Supporting text/controls remain 16px; composer and answers remain 18px.
- `npm test --prefix frontend -- --run`: 13/13 passed. Includes the existing conversation, ticket consent, failed save and failed login checks, plus new Dialog and mobile Sheet Escape/focus restoration tests. The category filter test now uses its correct radio role.
- `npm run build --prefix frontend`: TypeScript and production Vite build passed.
- Browser verified the real 29-source knowledge browser, Labs filtering, source dialog, Escape restoring the source button, and mobile Sheet dismissal restoring the menu trigger. Staff sign-in layout reviewed without saving credentials or generating tickets.
- No horizontal overflow at 375, 768, 1024, 1280 and 1440px. At 1280×720, the composer bottom was approximately 412px and all four topic cards fit (bottom approximately 708px). Mobile content scrolls vertically. Rechecked 18px composer text.
- Screenshots: `screenshots/shadcn-desktop.png`, `screenshots/shadcn-mobile.png`, `screenshots/shadcn-staff.png`.
- Backend behavior was unchanged; prior live context/consent results remain separate evidence. Browser 200% zoom and reduced-motion emulation remain manual checks as documented above.

## Paper-and-evergreen revision — 24 October 2026

The current interface and latest checks are recorded in `redesign-stages.md` and `redesign-browser-checks.json`. This supersedes the cobalt visual direction described above. The private GitHub repository is `imakshat27/campus-helpdesk`; baseline, design and implementation were pushed as separate checkpoints. Current screenshots use the `paper-` prefix.
