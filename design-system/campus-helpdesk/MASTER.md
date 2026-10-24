# Campus Helpdesk design system

User direction: professional and functional, with real solid colors; no pastel surfaces, gradients, glass effects, tiny text, or promotional filler. Revisited with UI UX Pro Max for contrast, clear action states, confirmation feedback and accessibility. Dataset marketing layouts and pale palette suggestions do not match this product and are excluded.

## Foundation

- Solid cobalt navigation `#163CDB`, white canvas/surfaces `#FFFFFF`, near-black text `#151923`, secondary text `#565F70`, neutral structural borders `#DCE0E7`.
- One strong blue area anchors the product: desktop sidebar; mobile top bar and drawer. All four topic icons use the same blue, without tinted tiles. White active navigation items; solid neutral hover feedback on white cards.
- Inter, locally bundled. Conversation and composer 18px; functional copy/controls 16px or larger. Main headings 34–40px depending on viewport; short laptop screens use 36px. Line height 1.65–1.8 for conversation text.
- Sidebar 256px; chat maximum outer width 896px, with 28–40px desktop gutters and 20px mobile gutters. Use compact vertical spacing on short laptop screens so the composer remains visible.
- 8–14px component corners and subtle neutral borders; minimal control shadows only. Lucide outline SVG icons, consistent size/stroke. Controls at least 44px.

## Interaction

- Direct chat home with a centered heading, composer as the primary element, and four compact editable topic cards below it. Persistent conversation and follow-up composer.
- Missing knowledge offers an inline ticket prompt. No ticket is created until “Yes, raise a ticket” is clicked or the user affirms the pending offer in chat. “No thanks” declines with no staff request. Explicit handoff from a supported answer also shows a confirmation before creating a ticket.
- Confirmation targets the specific question ID, not whichever question was most recently asked. Failed saves retain the offer and never claim success. Saved reference numbers appear on the corresponding answer.
- Read previous conversation for search: rewrite follow-ups into standalone questions, then revalidate prior citations if they are reused. Do not guess a subject or supply missing campus facts from general model knowledge.
- Source browser uses filters and readable rows. Source inspection uses shadcn Dialog (Radix) focus containment, Escape and focus restoration. Staff queue shows only real records.

## Review

Verify at 375, 768, 1024, 1440px and short laptop heights. Functional text must remain readable without horizontal overflow. Check rendered contrast (normal text at least 4.5:1), keyboard focus, mobile drawer focus, explicit ticket confirmation/decline, retained drafts and source detail. Respect reduced motion. The live context/consent test report is `reports/context-and-consent.md`.

## Component implementation

Use the committed shadcn/ui components in `frontend/src/components/ui`, configured through `frontend/components.json`. Button, Input, Textarea, Label, Card, Badge, Alert and Separator share semantic CSS variables. Sidebar uses the shadcn Sheet on mobile. Category filters use the single-select ToggleGroup with radio semantics and arrow-key navigation; staff status uses Tabs. Keep default readable controls at 16px and 44px minimum height. Source Dialog and mobile Sheet restore focus on dismissal. Do not reintroduce bespoke equivalents for these controls.
