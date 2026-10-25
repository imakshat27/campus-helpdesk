# Presentation and report

Prepared 25 October 2026 for the presentation on 26 October 2026.

- `presentation/campus-helpdesk-presentation-revised.pptx`: current presentation, 11 editable slides with presenter notes. Natural flow: problem, idea, approach, implementation, demonstration, current scope, proposed accounts and live staff chat, conclusion. Suggested duration: 7 to 8 minutes including the short demo. Development test counts are omitted.
- `presentation/campus-helpdesk-presentation.pptx`: earlier presentation retained for reference.
- `pdf/campus-helpdesk-project-report.pdf`: detailed project report with implementation, evidence, demonstration instructions and proposed future work.

The default demo declines the ticket offer and does not save a request. The optional staff extension creates a real demo ticket only after explicit confirmation. Recorded results are labelled separately from the planned live demo. No fresh paid model evaluation ran for artifact preparation.

Sources: project code, official-corpus reports, source manifest and deployment notes. Current isolated backend/frontend suites and production build were rerun. The latest fix still requires hosted end-to-end verification.

The revised deck also incorporates the user-provided **Two-account login and persistent live chat** plan. Exactly two fixed accounts, history across logins, and live staff takeover are explicitly proposed work, not current functionality. The PDF is the original report and has not been revised to incorporate this later plan. The current shared review-session gate is separate from the proposed account system.

Authoring sources are in `scripts/presentation/`. The PowerPoint builder uses the Artifact Tool presentation API; the report builder uses ReportLab. The screenshot is an actual capture of the deployed home screen on 25 October 2026. No source credentials belong in these artifacts.
