# Campus Helpdesk workspace

## Neon connection

Direct database access through `backend/.env` is configured and verified. The Neon plugin was used through OAuth during provisioning, but it reported as not installed at the end of setup. If its tools are unavailable, use SQLAlchemy from the backend environment; install and connect the plugin for its project-management tools. For this repository, always use the identifiers in `.neon/project.json`:

- Project: `campus-helpdesk` (`bold-glitter-68864438`)
- Branch: `main` (`br-dark-leaf-azodnawz`)
- Database: `campus_helpdesk`, Singapore (`aws-ap-southeast-1`)

Always pass this project ID explicitly to Neon tools that accept it. Other Neon projects in the account belong to separate applications. Do not modify them for this repository.

The backend connection is in the gitignored `backend/.env`. Never print database passwords, API keys, complete connection strings, or the contents of that file. Preserve unrelated settings when updating it. No credentials belong in `.neon/project.json` or source control.

Apply schema changes through Alembic from `backend/`. Use `uv run python -m app.seed` to load/update the approved sample sources. `uv run python -m app.evaluate` uses the configured OpenRouter model and creates real demo conversations plus tickets only after an explicit test confirmation; report results honestly. Run isolated backend tests with `uv run pytest -q`.

## UI

Follow `design-system/campus-helpdesk/MASTER.md` and the requested UI UX Pro Max skill when changing interfaces. Keep solid surfaces, readable text, restrained motion, and source-backed behaviour. Do not introduce gradients, glass effects, fabricated queue data, or simulated successful handoffs.

Conversation follow-ups must be resolved using actual history, never a word-count heuristic. Missing knowledge must return `needs_staff_confirmation` with no saved ticket; only explicit confirmation can create one. The escalation endpoint must require the specific user message ID and `confirmed: true`. Run `uv run python -m app.check_conversation` for the live context/consent regression (it confirms one demo ticket).
