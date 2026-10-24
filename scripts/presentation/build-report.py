"""Generate the project submission report using ReportLab, without service calls."""
from pathlib import Path
import html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/campus-helpdesk-project-report.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT_DIR=Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('Arial', str(FONT_DIR/'Arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold', str(FONT_DIR/'Arial Bold.ttf')))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial', boldItalic='Arial-Bold')
INK=colors.HexColor('#232B27'); GREEN=colors.HexColor('#294F40'); MUTED=colors.HexColor('#606861'); LINE=colors.HexColor('#DADDD5')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='Arial',fontSize=10.5,leading=16,textColor=INK,spaceAfter=10))
styles.add(ParagraphStyle(name='TitleX',fontName='Arial-Bold',fontSize=34,leading=39,textColor=GREEN,spaceAfter=18))
styles.add(ParagraphStyle(name='H1X',fontName='Arial-Bold',fontSize=23,leading=29,textColor=GREEN,spaceAfter=16))
styles.add(ParagraphStyle(name='H2X',fontName='Arial-Bold',fontSize=13,leading=18,textColor=INK,spaceBefore=12,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallX',fontName='Arial',fontSize=8.5,leading=12,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle(name='CellX',fontName='Arial',fontSize=9,leading=13,textColor=INK))
story=[]
def p(s,style='BodyX'):return Paragraph(s,styles[style])
def add(s,style='BodyX'):story.append(p(s,style))
def h(s):add(s,'H2X')
def page(n,title):
    if story:story.append(PageBreak())
    add(f'{n:02d}  /  PROJECT REPORT','SmallX');add(title,'H1X')
def table(headers,rows,widths):
    data=[[p(str(v),'CellX') for v in headers]]+[[p(str(v),'CellX') for v in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEEDE8')),('LINEBELOW',(0,0),(-1,0),.7,LINE),('LINEBELOW',(0,1),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,10))

page(1,'Campus Helpdesk')
add('Source-backed student support for VIT Vellore','TitleX')
add('Project report<br/>Presentation date: 26 October 2026<br/>Prepared: 25 October 2026')
add('<b>Independent academic prototype.</b> This project uses public university information. It is not an official VIT service and does not connect to private student records.')
h('Abstract')
add('Campus Helpdesk is a web prototype that combines a React question interface with retrieval-augmented generation (RAG), a searchable source library and a protected staff ticket queue. A FastAPI backend retrieves approved public VIT Vellore passages from Neon PostgreSQL with pgvector, requests structured answers through OpenRouter and validates citation identifiers. Students can inspect supporting passages and their original URLs.')
add('When evidence is missing, the application offers staff routing and waits for explicit consent. Conversation follow-ups use stored history. The implemented corpus contains 50 source documents, 1,073 searchable passages and 968 extractive Q&amp;A records, as recorded in the project validation reports. Evaluation distinguishes source retrieval, application behavior and generated-answer correctness.')
h('Report guide')
add('2 / Problem and scope &nbsp; 3 / Architecture &nbsp; 4 / Knowledge and retrieval<br/>5 / Implementation &nbsp; 6 / Verification &nbsp; 7 / Demonstration<br/>8 / Limitations and future work &nbsp; 9 / Conclusion and references','SmallX')

page(2,'Problem, objectives and scope')
h('Problem statement')
add('Students may need to search multiple public pages and policy PDFs to answer a campus question. A useful helpdesk should reduce this search effort while preserving the ability to inspect the original evidence. This is the project motivation, not a quantified finding from a student survey.')
h('Objectives')
table(['Objective','Implemented response'],[['Find campus information','Natural-language chat and searchable approved-source library.'],['Make answers inspectable','Source cards, supporting passages, original URLs and retrieval dates.'],['Support conversational use','History-based follow-up resolution and return to earlier topics.'],['Handle uncertainty','Clarification for incomplete questions and staff-confirmation offers for unsupported facts.'],['Control escalation','Explicit consent tied to the exact user message before saving a ticket.'],['Provide a staff workflow','Credential-protected ticket list, context inspection, resolve and reopen actions.']],[150,335])
h('Active scope')
add('The default knowledge mode is official public VIT Vellore material, imported on 24 October 2026. Coverage includes academics, library, hostels, welfare, procedures and other public services. Programme, student category and policy-year restrictions remain relevant. A retrieval timestamp does not guarantee that a policy is current.')
h('Excluded from the current implementation')
add('The system does not access attendance records, personal timetables, passwords, live room availability or account balances. It has no student login, university SSO, staff replies, email delivery or student notifications. Staff routing saves requests inside the application queue. It does not establish that an institutional office received or acted on them.')
add('The original fictional assignment corpus remains available only through explicit sample mode. Official-mode service failures do not restore fictional answers. [R1, R2]','SmallX')

page(3,'Architecture and data flow')
table(['Layer','Technology and responsibility'],[['Presentation','React 19, TypeScript, Vite, Tailwind and shadcn/Radix primitives. Chat, sources and staff pages. Vercel frontend configuration.'],['Application','FastAPI, Pydantic and SQLAlchemy. Conversation handling, retrieval orchestration, citation validation and ticket consent. Render backend configuration.'],['Answer provider','OpenRouter model configured in the backend. Structured outcomes and source IDs from supplied evidence.'],['Storage and retrieval','Neon PostgreSQL in Singapore, pgvector and 384-dimensional Sentence Transformers embeddings. Alembic migrations.']],[125,360])
h('Question processing')
add('<b>1. Receive and persist context.</b> The backend accepts the question and optional conversation UUID. It loads actual stored messages for that conversation.')
add('<b>2. Resolve the question.</b> For follow-ups, a model-based resolver forms a standalone retrieval query from bounded conversation history. Recent turns and early topic anchors help resolve references and topic returns.')
add('<b>3. Retrieve approved evidence.</b> Semantic and keyword candidates compete in a hybrid ranking. The backend can re-read previously cited passages and re-check approval before reuse.')
add('<b>4. Generate and validate.</b> OpenRouter returns an answer, clarification or unsupported result. The backend validates citation identifiers, applies bounded repair rules and constructs source cards from database records.')
add('<b>5. Respond or offer routing.</b> Supported answers include sources. Missing evidence returns <b>needs_staff_confirmation</b> without saving a ticket. Explicit consent triggers the persistence path.')
h('Deployment status')
add('Deployment URLs are recorded for the Vercel frontend and Render backend. A fresh home-screen capture succeeded during document preparation. This is narrower evidence than an end-to-end chat test. The latest unsupported-response fix passed local verification, while its hosted verification remains pending. [R1, R3, R8]')

page(4,'Knowledge preparation and retrieval')
table(['Recorded corpus measure','Value','Interpretation'],[['Approved public sources','50','VIT Vellore HTML and PDF documents.'],['Searchable passages','1,073','Heading/page-aware chunks stored with vectors.'],['Extractive Q&amp;A records','968','Section/page discovery questions with exact extracts.'],['Embedding dimensions','384','all-MiniLM-L6-v2 embeddings.'],['Returned passages','Up to 8','At most three passages from one document.']],[175,60,250])
h('Ingestion and provenance')
add('The importer follows allowlisted public VIT URLs, checks robots.txt and excludes portal/login paths. The manifest records original URLs, campus, retrieval timestamp, source format and SHA-256 hashes. Original downloads stay in a gitignored cache. Processed Markdown and extractive records are versioned. OCR supports scanned material such as the library policy, with a risk of extraction errors.')
h('Retrieval method')
add('Seeding splits text around headings or PDF pages into bounded passages of roughly 180 words. The retriever obtains up to 12 semantic candidates from pgvector and up to 30 keyword candidates. It combines cosine similarity and term overlap using a score of 0.8 semantic similarity plus 0.2 lexical overlap, then applies threshold and diversity rules. Narrow synonym expansion improves discovery without adding policy facts.')
h('Source controls')
add('Only approved documents participate in retrieval. Re-seeding official mode disables the prior sample corpus. Citation IDs must match available source passages. Source validation establishes provenance, but it cannot independently prove that every sentence follows from the cited text.')
h('Refresh process')
add('Refresh is manual: import_official --refresh, build_qna, then seed from the backend environment. Alembic handles schema changes. There is no scheduled source monitor. Critical fees, deadlines and policy decisions require checking the original document and its applicability. Counts above reflect recorded project validation rather than a fresh database recount for this report. [R2, R4]')

page(5,'Implementation and persistence')
table(['Entity','Main responsibility'],[['Document','Title, category, source content, approval, URL, campus and retrieval date.'],['Chunk','Document relationship, heading, passage text and vector embedding.'],['Conversation / Message','Conversation UUIDs, roles, message text, outcomes and cited-source snapshots.'],['Ticket','Reference, original query, conversation, reason and open/resolved status.']],[145,340])
h('Key API endpoints')
table(['Method and path','Purpose'],[['POST /api/chat','Question, optional conversation ID, structured outcome and source cards.'],['GET /api/knowledge','Search and category-filter approved documents.'],['GET /api/conversations/{id}','Retrieve stored conversation messages.'],['POST /api/conversations/{id}/escalate','Require a specific message_id and confirmed: true.'],['GET /api/staff/tickets','Credential-protected queue with status filter.'],['PATCH /api/staff/tickets/{id}','Resolve or reopen a ticket.']],[265,220])
h('Consent and failure behavior')
add('The application associates a ticket offer with the original question. Declining, greeting or thanking does not save a request. An escalation request must identify the exact user message and explicitly set the Boolean confirmation to true. A ticket reference appears only after a successful commit, and repeated requests can reuse an existing open ticket.')
h('Interface and access')
add('The interface uses readable paper surfaces and evergreen actions. Source dialogs retain policy headings and tables. Failed submissions preserve drafts. Staff credentials remain in UI memory and authenticate backend staff routes. Conversation UUIDs act as unguessable handles, but there is no student identity or ownership layer. Credentials and complete database URIs remain outside source control. [R1, R4]')

page(6,'Verification and results')
add('The following evidence has different scopes. Unit and component tests were rerun during preparation on 25 October 2026. Live-model and retrieval results come from the existing official-corpus reports. No new model evaluation or consent regression ran to create these documents.')
table(['Evidence','Result','What it establishes'],[['Backend isolated suite','77 passed','Application regressions using isolated test persistence and controlled dependencies.'],['Frontend suite','18 passed','Component/API behavior, including error and source workflows.'],['Production frontend build','Passed','TypeScript compilation and Vite production bundling.'],['Official retrieval checks','30 / 30','Expected source family appears in top eight for the selected questions.'],['Recorded live evaluation','12 / 12','Eight supported, two clarification and two unsupported outcome/source checks.'],['Recorded context / consent','8 turns passed','Follow-up, topic return, decline and one ticket after explicit confirmation.']],[150,85,250])
h('Interpretation')
add('The 30/30 retrieval result is a source-family recall check over a fixed question set. The 12/12 live result checks outcomes, source family and absence of unconfirmed tickets. Neither result means 100% factual answer accuracy or universal campus coverage. The live evaluator recorded unchanged ticket counts. The separate consent regression intentionally saved exactly one demo ticket after confirmation.')
h('Regression that matters')
add('An exact duplicate-ID-fee question exposed an unsupported provider response containing a valid but redundant citation. The validator now normalizes that unsupported shape and displays the fixed consent offer, while unknown citation IDs remain errors. Local tests and a live local request passed. The report still lists hosted verification of this fix as pending.')
h('Remaining validation')
add('Human factual review, full hosted chat/source/consent verification and a complete responsive/accessibility browser review remain open. The existing reports retain earlier failed live iterations, including transient provider/output errors. The single home-screen capture used in these deliverables does not replace those checks. [R3, R5-R8]')

page(7,'Short demonstration')
add('<b>Target duration: 2 minutes.</b> Present the deck in about 7 minutes overall. Open the application before speaking and allow the hosted backend time to wake. The sequence below is a presentation plan, not a newly executed test.')
table(['Time','Presenter action','Expected behavior to inspect'],[['0:00-0:30','Start a new conversation. Ask: What choices does FFCS give students?','An evidence-backed answer with a citation.'],['0:30-1:00','Open a source card and original link.','Supporting passage, URL and source/date context.'],['1:00-1:30','Ask: What choices does it give me?','The current conversation supplies the FFCS topic.'],['1:30-2:00','Ask: What is my personal attendance percentage today? Then choose No thanks.','An unsupported-information offer. Declining saves no ticket.']],[72,225,188])
h('Suggested narration')
add('“The assistant retrieves public campus sources before answering. I can inspect the evidence behind the response. The next question refers to our current topic, so the system uses conversation history. Personal attendance is outside the public corpus, so it asks whether I want staff support. I will decline here, so this step creates no ticket.”')
h('Optional staff extension')
add('If the presenter chooses to create a real demo request, explicitly confirm the relevant ticket offer, verify the saved reference, then open Staff using existing credentials. Show the real ticket context and resolve it if appropriate. This optional extension changes persisted demo data and is separate from the two-minute default flow. Never put staff credentials on slides or in screenshots.')
h('Fallback when the service is unavailable')
add('Show slide 7 and say: “These are recorded official-corpus results.” The existing live report shows FFCS course/time/load choices, “Which lab do you mean?” for an unnamed lab, and a staff-confirmation offer for personal attendance with no saved ticket. Do not present recorded text as a fresh live answer or a failed handoff as successful.')
add('Application: <link href="https://campus-helpdesk-rho.vercel.app" color="#294F40">campus-helpdesk-rho.vercel.app</link><br/>Evidence: reports/official-live-evaluation.md and reports/official-context-and-consent.md. [R5, R7]','SmallX')

page(8,'Limitations and proposed future work')
h('Current limitations')
add('Public information cannot answer private or real-time questions. Model output can still misinterpret a passage despite valid citations. OCR may introduce errors. Retrieved policies may belong to a different programme or academic year. Conversation memory is bounded: the application reads up to 80 stored messages and selects recent context with early anchors, rather than maintaining unlimited memory.')
add('The prototype has no student accounts or institutional identity integration. HTTP Basic staff access and UUID conversation handles are insufficient foundations for sensitive institutional use. There are no staff replies, email notifications or delivery guarantees outside the internal queue. Source refresh requires a manual run, and hosted flow validation remains incomplete.')
h('Proposed roadmap - not implemented')
table(['Priority','Proposed work','Completion evidence needed'],[['Before a pilot','Hosted end-to-end checks, responsive/accessibility review, staff source review.','Recorded browser/API outcomes and approved scope.'],['Before institutional use','SSO, role-based staff access, conversation ownership, rate limits and retention policy.','Identity/security review and access-control tests.'],['Workflow extension','Staff replies, student notifications and status tracking.','Delivery/error handling and consent tests.'],['Knowledge maintenance','Scheduled refresh, source-change review and stale-policy alerts.','Refresh audit trail and source approval process.'],['Evaluation expansion','Human-labelled answer benchmark and broader ambiguity/adversarial checks.','Sentence-level factual review and measured failure rates.'],['Optional approved integrations','Scoped access to university systems such as VTOP.','Institutional authorization and privacy assessment.']],[95,210,180])
add('These items define future work, not a committed timeline. The next practical milestone is a verified, staff-reviewed pilot using public information. No improvement in response time or staff workload is claimed without a measured deployment study. [R1-R3, R8]')

page(9,'Conclusion and evidence references')
add('Campus Helpdesk implements a complete prototype path from a public campus question to retrieved evidence, a cited answer and optional consent-based staff routing. The project also provides a searchable source library and a protected queue with ticket status changes. Its main contribution is the integration of source inspection, conversational context and explicit escalation consent in one working application.')
add('The evaluation supports the tested retrieval and application behaviors within the selected corpus and question sets. It does not establish universal factual correctness or production readiness. A staff-reviewed pilot, stronger identity controls and verified hosted workflows form the next stage.')
h('Project evidence index')
refs=[('R1','README.md','Project behavior, setup, scope and boundaries.'),('R2','reports/official-dataset.md','Corpus provenance, counts, method, failed iterations and limitations.'),('R3','DEPLOYMENT.md','Recorded deployment URLs, setup and pending hosted checks.'),('R4','backend/app/ and frontend/src/','Implementation reviewed for models, retrieval, APIs and UI behavior.'),('R5','reports/official-live-evaluation.md','Twelve recorded model/database checks and actual responses.'),('R6','reports/official-retrieval.md','Thirty source-family retrieval checks.'),('R7','reports/official-context-and-consent.md','Eight-turn regression and explicit demo-ticket consent.'),('R8','reports/unsupported-citation-fix.md','Latest unsupported-response fix and validation limits.'),('R9','knowledge/official/manifest.json','Original VIT source URLs, scope, hashes and retrieval metadata.')]
for key,path,desc in refs:add(f'<b>[{key}] {html.escape(path)}</b><br/>{desc}','SmallX')
h('Reproducibility')
add('From backend/: uv run pytest -q. From project root: npm test --prefix frontend and npm run build --prefix frontend. Existing live reports are included in reports/. Live evaluators consume provider resources, and app.check_conversation confirms one demo ticket. Run such checks deliberately and report their effects accurately.','SmallX')
add('Repository: imakshat27/campus-helpdesk (private). Source records imported 24 October 2026. Report prepared 25 October 2026 for the presentation on 26 October 2026. The artifact generation process did not expose credentials or query private student information.','SmallX')

def footer(c,doc):
    c.setFillColor(MUTED);c.setFont('Arial',8)
    c.drawString(55,813,'CAMPUS HELPDESK  /  PROJECT REPORT')
    c.setStrokeColor(LINE);c.line(55,802,540,802)
    c.drawString(55,30,'Independent prototype  /  26 October 2026')
    c.drawRightString(540,30,str(doc.page))
doc=SimpleDocTemplate(str(OUT),pagesize=(595.28,841.89),rightMargin=55,leftMargin=55,topMargin=57,bottomMargin=48,title='Campus Helpdesk - Project Report',author='Campus Helpdesk Project',subject='Implemented system, demonstration, verification and future work')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
