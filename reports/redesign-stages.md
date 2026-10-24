# Redesign stages — 24 October 2026

1. Baseline: preserve the working RAG application and shadcn UI in a new private GitHub repository. Credential scan passed; local `.env` excluded.
2. Design direction: replace the saturated navigation with paper/ink/evergreen, left-align the workspace, show concrete example questions and make sending explicit. See `design-system/campus-helpdesk/MASTER.md` for the student journey and component rules.
3. Implementation: apply the direction consistently to chat, knowledge, source inspection and staff access. Preserve history and explicit ticket consent.
4. Verification: frontend tests, production build, responsive browser checks and focus/contrast review. Commit the reviewed screenshots and results.

Each completed stage is committed and pushed to the private remote. Stage 1 baseline: `28fd62a`.
