# Campus Helpdesk design system

## Direction: paper, ink, evergreen

A quiet student support workspace. The interface should feel approachable and carefully arranged, with a clear next action and enough room to read. Use shadcn/ui components with a considered application layout. No gradients, glass, promotional copy, decorative statistics, fabricated activity or queue data.

The previous saturated sidebar competed with the work area. Replace it with a warm neutral navigation rail, a paper canvas and deep evergreen actions. Softness comes from restrained contrast between surfaces, generous spacing and rounded controls, not low-contrast text or tinted decorative cards.

## Foundation

- Canvas `#F8F7F4`, navigation `#EEEDE8`, white elevated surfaces `#FFFFFF`.
- Ink `#232B27`, supporting text `#606861`, evergreen actions `#294F40`, stronger hover `#203E33`, quiet borders `#DADDD5`.
- Selected navigation uses a white surface and evergreen text. Icons use a single Lucide family, without separate colored tiles for each topic.
- Inter, locally bundled, for controls and body. A restrained Georgia heading provides an editorial accent on the empty chat screen only; app pages use Inter. Functional text is at least 16px, answers/composer 18px. Heading 36–46px, comfortable reading measure.
- Desktop navigation 248px. Main chat content max-width 816px including gutters, aligned left within its column. At short laptop heights, preserve access to the composer and topic suggestions. Mobile navigation uses shadcn Sheet.
- Corners 10–16px; composer 18px. Single restrained shadow on the composer/dialog, no embossed effects. All actions have visible keyboard focus and minimum 44px targets.

## Student journey

1. Arrive at a useful prompt, a short explanation and a clearly labelled question box. The heading is aligned to the question box, without a repeated large brand icon.
2. Type a question or choose one of four concrete examples. Topic suggestions prefill the box so the student can edit before sending. Each shows its actual sample question, rather than vague feature descriptions.
3. A labelled send action makes submission obvious. Shift+Enter inserts a new line; Enter sends. Disable submissions while pending, retain the question if the request fails, and allow correction/retry.
4. Read the answer at 18px with clear author separation. Inspect a source in a keyboard-accessible Dialog. Source titles and supporting passages stay readable.
5. If information is unavailable, offer a ticket and wait for explicit consent. Ticket actions are grouped under the relevant question. A failed save retains the offer and never claims success.

Keep demo provenance visible in one quiet navigation note and an accurate reference-date caption, without repeated badges competing with the main action. These sources are sample campus information, not official VIT policy.

## Knowledge and staff

- Search comes before category filtering and results. A single-select ToggleGroup has radio semantics and keyboard navigation. Result rows show title, category/type and an excerpt; no decorative tile grid.
- Source Dialog uses Radix focus containment, Escape and focus restoration.
- Staff sign-in is a small, clearly labelled form on a white Card. Staff status uses Tabs. Display only real tickets. Resolve actions report actual persistence.

## Preserved behavior

- Resolve follow-ups using actual conversation history, never a word-count heuristic. Revalidate approved source chunks before reusing citations.
- Missing knowledge returns `needs_staff_confirmation`, with no ticket saved. Only explicit consent creates a ticket for the original message ID, with `confirmed: true`.
- Service failures remain distinct from missing campus information. Declining or greeting never creates a staff request.

## Review

Check 375, 768, 1024 and 1440px, plus 1280×720. No horizontal overflow; minimum 16px functional text and 18px chat. Verify contrast, keyboard order, Dialog/Sheet focus return, failed requests, sources and consent. Respect reduced motion. Record actual browser checks separately from automated tests and manual checks still pending.

## Official knowledge and source UX

The active collection is now downloaded public VIT Vellore material. Replace demo hints with academics, library, hostel and welfare examples. Display the source URL and retrieval date, retaining publication years in policy text. Never substitute sample facts during a network failure. Source detail renders headings, lists and tables with readable text; original PDF/page links let students verify critical details. Group answer citations by document while retaining all cited passages. Knowledge filters derive from the actual categories; show 15 results at a time and let users request more. Preserve unsent drafts through navigation and clear them only for a new conversation. Older fictional conversation cache uses a different storage key.

## Account login and live support

One shared username/password form serves the two fixed accounts. Role-specific navigation hides staff access from students and takes staff directly to the queue. Conversation history belongs to the signed-in student and loads from the backend. Local drafts are scoped to account and conversation.

Show AI, waiting-for-staff, staff-active and resolved states in plain text. A confirmed handoff pauses AI; a staff member must select Start chat before replying. Label AI and staff authors separately, with timestamps. Resolved chats show an explicit Reopen action and disable sending. Connection status describes actual WebSocket state; disconnection preserves drafts and offers reconnection, without inventing staff presence. Human chat captions describe saved messages rather than promising AI citations.
