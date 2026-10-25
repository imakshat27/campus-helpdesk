# Campus Helpdesk design system

## Direction: a quiet support workspace

Use a minimal application layout with a white work surface, a neutral navigation rail, dark readable type, thin separators, and restrained evergreen actions. Keep the interface useful and direct. Avoid oversized landing-page headings, decorative icon tiles, redundant captions, card grids, gradients, glass effects, and fabricated activity or queue data.

## Foundation

- Use the supplied Clear Pro Pan European font throughout. The original font folder is preserved at `frontend/src/assets/fonts/clear-pro/`. Local `@font-face` declarations load regular (400), medium (500), semibold (600), bold (700), and regular italic with `font-display: swap`. No remote font service or alternate serif heading.
- Work surface `#FFFFFF`; navigation `#F8F9F8`; supporting surfaces `#F5F6F5`; ink `#232B27`; supporting text `#606861`; evergreen actions/focus `#294F40`; borders `#E0E4E0`.
- Functional text is at least 16px; message and source text is 18px. Headings are 28–30px, with 500–600 weight for hierarchy. Body line height is 1.6–1.7 and reading measure is approximately 65–75 characters.
- Desktop navigation is 240px (220px on smaller laptops). Header height is 64px. Chat has an 800px content measure including its internal layout; page content stays aligned and readable.
- Controls have 44px minimum targets and visible keyboard focus. Use 4–8px corners and no decorative shadows. Lucide icons serve navigation or actions, rather than filling branded tiles.
- Motion is limited to normal interaction feedback. Respect reduced motion.

## Screens

- Sign-in: a compact, centered form with the Campus Helpdesk wordmark, campus name, a short heading, visible username/password labels, and inline errors. No promotional panel or security illustration.
- Student start: a modest heading, one sentence of context, the labelled composer, and four useful suggested questions. Suggestions show their actual question and prefill the input so it can be edited before submission.
- Conversation: text author labels and timestamps separate student, AI, and staff messages. The transcript scrolls independently while the composer stays visible in the normal layout. A single status row conveys AI, waiting, staff-active or resolved state. Keep connection state accurate and accessible; on mobile its labelled indicator avoids crowding the header.
- Knowledge base: search, a labelled native topic select, actual source/result counts, and plain rows separated by rules. Show 15 results at a time with Show more. Source details retain headings, tables, original links, campus and retrieval date, with keyboard dismissal and focus return.
- Staff queue: simple underlined status tabs and real request rows with references, dates and readable status labels. Empty states describe actual queue state without decorative statistics.

## Preserved behavior

Student and staff use the shared account login, with role-specific navigation. Account-owned history loads from the backend, and drafts remain scoped to account and conversation. Failed sends retain drafts and retry identifiers. Enter sends; Shift+Enter adds a line.

Follow-ups use actual conversation history, never a word-count heuristic. Only approved official VIT Vellore sources establish facts; preserve programme, campus and policy-year scope, publication years, source URLs and retrieval dates. Never substitute the fictional sample corpus after a network failure. Revalidate source passages before reuse and retain all cited passages when grouping by document.

Missing information returns `needs_staff_confirmation` without saving a ticket. Explicit handoff requires the original message ID and `confirmed: true`; declining never creates a request. A failed save never claims success. Confirmed handoff pauses AI; staff must Start chat before replying. Resolved conversations disable sending and offer explicit reopening. Connection loss must not imply successful delivery or staff availability.

## Review

Verify 375, 768, 1024, 1440px and 1280×720: no horizontal overflow, readable text, accessible controls, and a visible composer. Check the actual Clear Pro font load, source table scrolling, failed requests, consent, independent role sessions, reconnect recovery, keyboard focus, Dialog/Sheet Escape behavior, and reduced motion. Record browser observations separately from automated tests and hosted verification still pending.

Chat scrolling: open saved history at the latest message. Sending scrolls to the sent message for both roles. Follow incoming messages only when the reader is within 64px of the bottom; otherwise preserve their position and show a New messages button. Keep the transcript pinned through composer and viewport resizing when already at the bottom.
