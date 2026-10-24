# VIT Vellore public knowledge corpus

This collection was downloaded from the public `vit.ac.in` website on 24 October 2026 at the user's request. Original copyright belongs to VIT and the respective authors. It is an independent student helpdesk index, not a VIT publication or official VIT chatbot.

- `manifest.json`: original URLs, campus scope, retrieval timestamps, SHA-256 of downloaded originals, and excluded/failed URLs.
- `processed/`: extracted Markdown with headings, tables and PDF page references. A few scanned pages use local Tesseract OCR; OCR can contain transcription errors. Consult the original PDF for critical details.
- `qna.json`: extractive question/passage records generated from sections. Answers are source extracts, not invented question-answer pairs. Section/page prompts are for discovery, not independently reviewed FAQ assertions.
- `raw/`: downloaded originals cached locally and excluded from Git. Rebuild using `uv run python -m app.import_official` from `backend/`; use `--refresh` to fetch again. This is a bounded public-source importer that checks robots.txt and never logs into VTOP or another portal.

Then run `uv run python -m app.build_qna` and `uv run python -m app.seed`. The default `KNOWLEDGE_MODE=official` deactivates the fictional sample corpus before activating imported sources. `KNOWLEDGE_MODE=sample` restores the original assignment demo. Never combine fictional fees/room/lab timings with official policy answers.

Retrieval timestamps are not publication dates. Documents may be tied to a particular year, programme or campus. Older regulations are retained with their original titles/content and should be cited with that qualification. A linked library policy may differ from a current page; the assistant must disclose conflicting information. No completeness guarantee is made: personal schedules, attendance, private records, live lab availability and event registration require authenticated university systems or staff.

Sources are selected from public institutional pages for this prototype; this is not a staff-reviewed policy approval process. Re-running the importer is an explicit refresh, not a background monitor. The checked-in manifest records the run actually used.

Scanned-PDF extraction uses optional local `pdftoppm` (Poppler) and `tesseract` executables. Install both to reproduce OCR from scratch. When unavailable, the importer records an exclusion instead of treating an image-only PDF as extracted text. Processed PDF cache reuse requires matching the original SHA-256 in the manifest, preventing reuse of old text after an original file changes.
