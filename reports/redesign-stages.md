# Redesign stages — 24 October 2026

1. Baseline: preserve the working RAG application and shadcn UI in a new private GitHub repository. Credential scan passed; local `.env` excluded.
2. Design direction: replace the saturated navigation with paper/ink/evergreen, left-align the workspace, show concrete example questions and make sending explicit. See `design-system/campus-helpdesk/MASTER.md` for the student journey and component rules.
3. Implementation: apply the direction consistently to chat, knowledge, source inspection and staff access. Preserve history and explicit ticket consent.
4. Verification: frontend tests, production build, responsive browser checks and focus/contrast review. Commit the reviewed screenshots and results.

Each completed stage is committed and pushed to the private remote. Stage 1 baseline: `28fd62a`.

## Completed checkpoints

- Baseline `28fd62a`: complete application preserved and pushed; repository visibility verified private.
- Direction `5a3c1b5`: theme, student journey and future commit/push instructions saved and pushed.
- Implementation `c3f391a`: new layout/theme and clearer example/send actions pushed after frontend tests passed.
- Review checkpoint: fixed source-list overflow, search input naming, redundant source headings and manual handoff focus. Saved browser evidence and reran checks before pushing.

## Verification

- Frontend: 13 tests passed, including source/Sheet focus restoration, retained failed drafts, conversation continuity, explicit ticket consent and manual handoff focus/decline. TypeScript and production build passed.
- Backend: 43 isolated tests passed. The live nine-turn context/consent check passed and created exactly one demo ticket after explicit test consent. Updated results are in `context-and-consent.md`.
- Browser chat: no horizontal overflow at 375, 768, 1024, 1280 and 1440px. At 1280×720, composer bottom ~431px and examples bottom ~715px. Mobile content scrolls vertically; composer text is 18px.
- Browser knowledge and staff sign-in: no horizontal overflow at 375, 768, 1024 and 1440px. Real source search/filtering, source detail and focus return verified. Mobile Sheet Escape returned focus to the navigation trigger.
- Rendered home text: 32 visible text elements measured, minimum contrast 4.91:1, minimum size 16px; disabled controls excluded. This is a targeted home check, not a full accessibility audit.
- Real SJT 301 answer and citations displayed in the browser. An initial request timed out with the draft retained; retry succeeded. A separate request through the Vite proxy returned 200 in ~28.6s. No successful handoff was simulated.
- Manual browser 200% zoom and reduced-motion emulation remain pending, as documented in `verification.md`.
- Evidence: `redesign-browser-checks.json` and `screenshots/paper-{desktop,mobile,answer,knowledge,staff}.png`.
