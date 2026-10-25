"""Build the presentation-day report. No database or model calls."""
from pathlib import Path
import html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/campus-helpdesk-project-report-black-and-white.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
FD=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Arial','Arial.ttf'),('Arial-Bold','Arial Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(FD/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
NAVY=colors.black; TEAL=colors.black; MUTED=colors.HexColor('#444444'); LIGHT=colors.black; LINE=colors.HexColor('#CCCCCC'); PAPER=colors.white
S={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10.5,leading=16,textColor=NAVY,spaceAfter=11),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=26,leading=31,textColor=NAVY,spaceAfter=19),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=13,leading=18,textColor=TEAL,spaceBefore=14,spaceAfter=8),
 'kicker':ParagraphStyle('kicker',fontName='Arial-Bold',fontSize=9,leading=14,textColor=TEAL,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=8.5,leading=12,textColor=MUTED,spaceAfter=8),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=9.5,leading=14,textColor=NAVY),
 'headcell':ParagraphStyle('headcell',fontName='Arial-Bold',fontSize=9.5,leading=14,textColor=colors.black),
 'cover':ParagraphStyle('cover',fontName='Arial-Bold',fontSize=58,leading=63,textColor=colors.black,spaceAfter=22),
 'coversub':ParagraphStyle('coversub',fontName='Arial',fontSize=20,leading=29,textColor=LIGHT,spaceAfter=22),
 'coverbody':ParagraphStyle('coverbody',fontName='Arial',fontSize=11,leading=18,textColor=LIGHT,spaceAfter=13),
 'coverlabel':ParagraphStyle('coverlabel',fontName='Arial-Bold',fontSize=10,leading=15,textColor=LIGHT,spaceAfter=17),
}
story=[]
def p(v,style='body'):return Paragraph(v,S[style])
def add(v,style='body'):story.append(p(v,style))
def h(v):add(v,'h2')
def page(n,title):
 if story:story.append(PageBreak())
 add(f'{n:02d} / PROJECT REPORT','kicker');add(title,'h1')
def table(headers,rows,widths):
 data=[[p(str(x),'headcell') for x in headers]]+[[p(str(x),'cell') for x in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEEEEE')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PAPER]),('LINEBELOW',(0,1),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 story.append(t);story.append(Spacer(1,12))

add('VIT VELLORE / INDEPENDENT ACADEMIC PROJECT','coverlabel')
story.append(Spacer(1,34))
add('Campus<br/>Helpdesk','cover')
add('AI answers with sources.<br/>Staff support in the same conversation.','coversub')
story.append(Spacer(1,25))
add('PROJECT REPORT<br/>Presentation: 25 October 2026','coverlabel')
add('Campus Helpdesk combines a conversational AI assistant, an inspectable public-source library and a consent-based route into live staff support. Two fixed accounts give students and staff their own workspaces, with saved conversations across logins.','coverbody')
add('The system uses React, FastAPI and Neon PostgreSQL with pgvector. Retrieved VIT Vellore passages support AI answers. When a student confirms a handoff, AI pauses and staff continues the conversation.','coverbody')
add('This is an independent prototype, not an official university service. Broader rollout, scheduled source refresh and university integration remain future work.','coverbody')

page(2,'The problem and the idea')
h('Problem')
add('Students may need to search several university pages and policy PDFs to answer an everyday campus question. Even after finding a relevant document, they must identify its campus, programme and academic-year scope. Unpublished details and personal cases still need staff help. This motivates the project; it is not a finding from a measured student survey.')
h('Idea')
add('Provide one place to ask a question, inspect the supporting source and continue with staff when needed. AI handles questions supported by public campus material. Students control whether a question leaves AI assistance and enters the staff queue.')
table(['Need','Project response'],[['Find information','Natural-language chat and a searchable official-source library.'],['Check an answer','Supporting passages, original URLs and retrieval dates.'],['Continue a discussion','Conversation context and saved history after signing in again.'],['Get human support','Explicitly confirmed handoff, a waiting state and live staff chat.'],['Track progress','Distinct AI/staff replies and conversation resolution.']],[140,345])
h('Delivered scope')
add('The delivered version has exactly two accounts: one student and one staff account. It supports source-backed AI questions, saved conversations, role-specific access and live human takeover. The project owner confirmed the account, history and live-chat implementation as complete and verified on 25 October 2026. [R10]')
h('Report guide')
add('3 / Architecture &nbsp; 4 / Knowledge &nbsp; 5 / Accounts and live handoff<br/>6 / Evidence &nbsp; 7 / Demo &nbsp; 8 / Future scope &nbsp; 9 / Conclusion and references','small')

page(3,'Architecture and answer flow')
table(['Layer','Role'],[['React + TypeScript','Student chat, source inspection, saved history and staff workspace.'],['FastAPI + Python','Authentication, ownership, conversation handling and consent.'],['Neon PostgreSQL + pgvector','Persistent source passages, vectors, messages and support records.'],['OpenRouter','Structured AI responses grounded in retrieved passages.'],['HTTP + WebSocket delivery','Authenticated message submission and live updates after persistence.']],[175,310])
h('During AI assistance')
add('<b>1. Understand context.</b> The assistant uses the current question and actual conversation history to resolve references and follow-ups.')
add('<b>2. Retrieve evidence.</b> Semantic and keyword search select relevant approved Vellore source passages. Previously cited material must still be approved before reuse.')
add('<b>3. Generate and validate.</b> The model returns a structured outcome and source identifiers. The backend validates citations and builds source cards from known records.')
add('<b>4. Answer or clarify.</b> Supported questions receive cited answers. Ambiguous questions request detail. Missing evidence leads to an offer of staff support, without saving a ticket before consent.')
h('During staff assistance')
add('Explicit confirmation moves the conversation into the waiting state. Staff accepts the request and continues live, while AI remains paused. Messages persist in Neon before delivery updates reach the clients. Resolution closes the current chat, with an explicit reopen option. [R4, R10]')
add('Vercel frontend and Render backend configuration are recorded in the repository. Team-confirmed extension status is separate from the older local checkout and its earlier verification reports. [R3, R10]','small')

page(4,'Knowledge and source grounding')
add('The active collection uses public VIT Vellore HTML and PDF material imported on 24 October 2026. The original fictional assignment corpus remains separate and inactive in official mode. Service failures do not substitute fictional answers.')
table(['Recorded measure','Value'],[['Approved public source documents','50'],['Searchable passages','1,073'],['Extractive Q&amp;A records','968'],['Embedding dimensions','384'],['Returned passages','Up to eight, with at most three from one document']],[290,195])
h('Preparation')
add('The importer follows allowlisted public VIT URLs and excludes portal/login paths. It records original URLs, campus, retrieval dates, formats and file hashes. Heading/page-aware splitting preserves context, while OCR makes scanned material searchable. OCR remains a possible source of extraction errors.')
h('Retrieval')
add('Sentence Transformers embeddings support semantic search through pgvector. Keyword matches complement vector candidates. The retriever combines semantic similarity with term overlap, removes duplicate content and limits how much any one document dominates the answer context.')
h('Source inspection')
add('Students can read supporting passages and open original links. A valid citation establishes provenance, but it does not prove that every generated sentence correctly follows from that passage. Fees, deadlines and other critical details still require attention to programme and year.')
h('Maintenance boundary')
add('Refresh currently requires a manual import, extraction and seed run. Scheduled refresh with review of source changes belongs to future scope. The counts above come from the recorded corpus validation, not a new database recount for this revision. [R2, R9]')

page(5,'Accounts, history and live handoff')
h('Two role-specific workspaces')
add('One shared login screen serves the student and staff accounts. Students start or resume their own conversations. Staff sees confirmed requests and the relevant conversation context. Login sessions remain distinct from conversations, so signing out does not erase saved chat history. [R10]')
table(['State','Behaviour'],[['AI assistance','The student asks questions and receives source-backed AI answers.'],['Waiting for staff','The student confirms a handoff. Save the ticket and pause AI replies.'],['Staff active','Staff selects Start chat. Both accounts exchange live messages.'],['Resolved','Staff closes the conversation. The student can reopen it into the queue or start a new AI conversation.']],[145,340])
h('Consent and persistence')
add('A handoff identifies the exact originating question and requires explicit confirmation. Offers and declines never create tickets. The design keeps one active support ticket per conversation, preserves citations and labels staff replies separately from AI answers. Messages save before they broadcast to connected clients.')
h('Delivery and recovery')
add('Authenticated HTTP handles sends, while a WebSocket carries committed message and status updates. Stable message identifiers, ordered history and retry identifiers prevent duplicate sends. Reconnect recovery reloads authoritative history and queue state, with visible errors and retained drafts.')
h('Boundaries of this version')
add('The initial scope uses two fixed accounts and one backend worker. It does not include public registration, password reset, typing indicators, attachments, read receipts or token-by-token AI streaming. The functional extension is complete and verified according to the project owner. The detailed design comes from the supplied implementation specification. [R10]')

page(6,'Evidence and evaluation')
h('Evidence basis')
add('This report combines repository evidence for the original RAG and ticket workflow with the project owner\'s 25 October 2026 confirmation that the teammate\'s two-account login, saved history and live staff chat are complete and verified. The teammate\'s completed build is not reflected in the local checkout reviewed for this revision. No fresh independent extension test is claimed here. [R10]')
table(['Evidence','What it supports'],[['Recorded retrieval evaluation','Expected source families appeared in the top eight for 30 selected questions.'],['Recorded live answer evaluation','Twelve selected questions covered supported answers, clarification and unavailable facts.'],['Recorded context/consent check','Follow-ups, a topic return, a decline and a ticket after explicit consent.'],['Earlier isolated application checks','Backend, frontend and production-build checks for the earlier code version.'],['Team confirmation, 25 October','Completed and verified login, saved conversations and live staff takeover.']],[185,300])
h('Interpretation')
add('Retrieval success means the expected source family appears in the search results. It does not establish universal answer correctness. Automatic live checks cover outcome and source family rather than independent sentence-level factual review. Earlier failed iterations remain documented in the official-dataset report.')
h('Verification boundaries')
add('The earlier reports remain evidence for their tested versions and do not automatically become test records for the new extension. The report distinguishes those results from the team-confirmed delivery status. Institutional use still calls for broader factual review, accessibility checks and operational validation.')
add('No live model calls, account logins or demo tickets ran as part of this document revision. [R2, R5-R8, R10]','small')

page(7,'Short demonstration')
add('<b>Target: 2 to 3 minutes.</b> Prepare separate student and staff browser sessions before presenting. Use a normal campus question and an explicitly confirmed demo handoff. Keep credentials out of the projected view.')
table(['Step','Presenter action','Visible result'],[['1 / Ask','Student asks: What choices does FFCS give students? Open a citation.','AI answer, supporting passage and source link.'],['2 / Resume','Sign back in and reopen a saved conversation.','Earlier messages and citations remain available.'],['3 / Handoff','Student asks for staff help and explicitly confirms.','Waiting state and a saved support request. AI pauses.'],['4 / Reply','Staff selects Start chat and sends a brief reply.','The student sees a distinct staff reply live.'],['5 / Resolve','Staff resolves the conversation.','Closed composer and an explicit reopen option.']],[67,235,183])
h('Suggested narration')
add('“The student checks the AI answer against its source, returns to saved history and confirms a handoff. AI pauses while staff continues the same conversation live.”')
h('Demo preparation')
add('Prepare a saved conversation and use an ordinary campus question. Confirming the handoff saves or reuses a real demo ticket. Resolve it afterward. Verify visible delivery before claiming a send succeeded.')
h('Fallback')
add('If the service is unavailable, describe the team-verified workflow and label recorded material accurately. The earlier source-screen screenshot does not show the new account or staff-chat interface. This is a runbook, not a fresh test record.')
add('Presentation date: 25 October 2026. Public frontend recorded in deployment notes: <link href="https://campus-helpdesk-rho.vercel.app" color="#000000">campus-helpdesk-rho.vercel.app</link>. Use the teammate-verified build for the account/live-chat demonstration. [R3, R10]','small')

page(8,'Limitations and future scope')
h('Current limitations')
add('The corpus contains public information and cannot retrieve private VTOP records, personal attendance or live room availability. Policies can differ by programme, student category and academic year. Model interpretation and OCR can introduce errors. Conversation context is bounded, and staff response time depends on availability.')
add('The two fixed accounts demonstrate the complete student/staff journey. They do not constitute institution-wide identity provisioning. The single-worker real-time design also needs additional event distribution before multiple backend workers can share live connections. [R2, R10]')
h('Future scope beyond the completed version')
table(['Area','Next work'],[['Broader rollout','Support more users, departments and staff routing. Validate capacity and multi-worker delivery.'],['Source maintenance','Schedule official-source refresh, detect changes and require review before publishing updates.'],['University integration','Add institutional sign-in and authorized, scoped access to university systems.'],['Institutional readiness','Agree privacy and retention rules. Complete staff source review and wider accessibility checks.']],[145,340])
h('Progression toward a campus pilot')
add('The next milestone is a wider staff-reviewed pilot using the completed account and live-chat workflow. Private-system integrations require institutional approval and appropriate privacy controls. No delivery schedule or measured staff-workload reduction is claimed.')
add('Two-account login, saved conversations and live staff messaging are completed features. They are intentionally excluded from this future-work list. [R10]','small')

page(9,'Conclusion and references')
add('Campus Helpdesk brings public-information search, source-backed AI answers and live staff support into one conversation. The delivered two-account version includes saved history, explicit handoff consent, staff takeover and resolution. This supports a complete student-to-staff demonstration while keeping the boundary between public knowledge and personal cases visible.')
add('The next stage is broader rollout, scheduled knowledge maintenance and approved university integration. The project remains an independent academic prototype. Its evaluation evidence has defined limits, and team-confirmed completion is separate from a new independent test run.')
h('Evidence index')
refs=[('R1','README.md','Base project purpose and RAG behaviour.'),('R2','reports/official-dataset.md','Corpus method, counts and limitations.'),('R3','DEPLOYMENT.md','Recorded URLs and earlier deployment status.'),('R4','backend/app/ and frontend/src/','Earlier local implementation reviewed.'),('R5','reports/official-live-evaluation.md','Recorded official-corpus model outcomes.'),('R6','reports/official-retrieval.md','Source-family retrieval evaluation.'),('R7','reports/official-context-and-consent.md','Recorded context and consent workflow.'),('R8','reports/unsupported-citation-fix.md','Earlier unsupported-answer regression and validation.'),('R9','knowledge/official/manifest.json','Source provenance and retrieval metadata.'),('R10','Project owner confirmation and supplied implementation specification','Two-account login and persistent live chat. Completion and verification confirmed on 25 October 2026; future scope clarified the same day.')]
for key,path,desc in refs:add(f'<b>[{key}] {html.escape(path)}</b><br/>{desc}','small')
h('Version note')
add('Prepared and presented: 25 October 2026. This edition supersedes the earlier report dated for 26 October. The account/live-chat status uses the owner\'s latest confirmation. No credentials or complete database connection strings belong in the report.','small')

def cover(c,doc):
 c.setFillColor(colors.white);c.rect(0,0,595.28,841.89,fill=1,stroke=0)
 c.setFont('Arial',8);c.setFillColor(LIGHT);c.drawString(55,29,'CAMPUS HELPDESK / 25 OCTOBER 2026');c.drawRightString(540,29,'01')
def footer(c,doc):
 c.setFillColor(MUTED);c.setFont('Arial',8);c.drawString(55,812,'CAMPUS HELPDESK / PROJECT REPORT');c.drawRightString(540,812,'25 OCTOBER 2026')
 c.setStrokeColor(LINE);c.line(55,800,540,800);c.drawString(55,29,'Independent academic prototype');c.setFillColor(TEAL);c.setFont('Arial-Bold',10);c.drawRightString(540,29,f'{doc.page:02d}')
doc=SimpleDocTemplate(str(OUT),pagesize=(595.28,841.89),rightMargin=55,leftMargin=55,topMargin=61,bottomMargin=52,title='Campus Helpdesk - Project Report - 25 October 2026',author='Campus Helpdesk Project',subject='Implemented AI, account history and live staff support, with future scope')
doc.build(story,onFirstPage=cover,onLaterPages=footer)
print(OUT)
