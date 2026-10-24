import fs from 'node:fs/promises';

// Authored against the Artifact Tool presentation API. All slide text is editable.
export async function buildDeck(presentation, root) {
  presentation.slides.keep([]);
  const C={paper:'#F8F7F4',ink:'#232B27',muted:'#606861',green:'#294F40',white:'#FFFFFF'};
  const font='Arial';
  presentation.theme.defaultFont=font;
  function text(s,value,x,y,w,h,size=28,color=C.ink,bold=false){
    const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    sh.text=value; sh.text.style={typeface:font,fontSize:size,color,bold};return sh;
  }
  function slide(section,title,n,dark=false){
    const s=presentation.slides.add({width:1280,height:720});s.background.fill=dark?C.green:C.paper;
    text(s,section.toUpperCase(),72,38,1100,30,18,dark?'#DBE6DD':C.green,true);
    text(s,title,72,100,1136,112,46,dark?C.white:C.ink,true);
    text(s,`CAMPUS HELPDESK     /     ${String(n).padStart(2,'0')}`,72,671,1100,24,14,dark?'#DBE6DD':C.muted);
    return s;
  }
  function notes(s,body,refs){s.speakerNotes.text=body+'\n\nProject evidence: '+refs.join(', ')+'. Repository: imakshat27/campus-helpdesk. Prepared 25 October 2026 for presentation on 26 October 2026.';}
  function row(s,num,title,body,y,w=1100){text(s,num,72,y,65,50,30,C.green,true);text(s,title,158,y,w-100,44,29,C.ink,true);text(s,body,158,y+48,w-100,78,25,C.muted);}

  let s=slide('Project presentation','Campus Helpdesk',1,true);
  text(s,'Source-backed student support\nfor VIT Vellore',72,250,1050,140,48,C.white);
  text(s,'26 October 2026',72,490,1000,40,25,'#DBE6DD');
  text(s,'Independent academic prototype',72,548,1100,38,24,'#DBE6DD');
  notes(s,'Opening, 20 seconds. Introduce a working web prototype that answers public campus questions with inspectable sources and asks for consent before creating a staff ticket. It is independent of VIT. Suggested total: 7 minutes, including a 2-minute live demonstration.', ['README.md']);

  s=slide('01  Problem and scope','Student questions and project scope',2);
  row(s,'01','Problem','Campus information spans web pages, policy PDFs and different offices.',224);
  row(s,'02','Objective','Provide one question interface with evidence students can inspect.',363);
  row(s,'03','Boundary','Public Vellore information. Personal VTOP records remain unavailable.',502);
  notes(s,'40 seconds. Explain the information-finding problem as the design motivation, not a measured survey result. The project does not access private attendance, personal timetables or live allocations. Roadmap: scope, implementation, demonstration, evidence and future work.',['README.md','reports/official-dataset.md']);

  s=slide('02  Implemented system','Implemented features',3);
  text(s,'Student workspace',72,224,680,48,32,C.green,true);
  text(s,'Cited chat answers and source inspection\nConversation follow-ups and topic returns\nSearchable official-source knowledge base',72,287,700,183,29);
  text(s,'Staff workflow',72,492,680,48,32,C.green,true);
  text(s,'Explicit ticket consent, protected queue,\nresolve and reopen actions',72,548,720,85,29);
  const b=await fs.readFile(root+'/scripts/presentation/assets/helpdesk-home.png');
  s.images.add({dataUrl:'data:image/png;base64,'+b.toString('base64'),contentType:'image/png',alt:'Actual deployed Campus Helpdesk home screen captured 25 October 2026',fit:'contain',position:{left:875,top:204,width:265,height:430}});
  notes(s,'40 seconds. These capabilities exist in the source code. Screenshot: actual deployed home screen captured 25 October 2026, with no generated answers or fabricated queue. Staff access uses configured HTTP Basic credentials. No student account system exists.',['frontend/src/App.tsx','backend/app/main.py','backend/app/schemas.py']);

  s=slide('02  Implemented system','Architecture and answer flow',4);
  row(s,'01','React interface  /  Vercel','Student chat, knowledge browser and staff workspace',224);
  row(s,'02','FastAPI backend  /  Render','History resolution, hybrid retrieval, OpenRouter generation and validation',363);
  row(s,'03','Neon PostgreSQL with pgvector','Approved documents, 384-dimensional vectors, conversations and tickets',502);
  notes(s,'45 seconds. A question reaches FastAPI. For follow-ups, the resolver uses actual stored history to form a search query. Retrieval combines vector similarity and keyword matching. OpenRouter generates structured output from passages. The server validates citation IDs before returning source cards. Alembic manages schema changes. Frontend and backend have separate deployment configurations.',['backend/app/main.py','backend/app/retrieval.py','backend/app/llm.py','backend/app/models.py','DEPLOYMENT.md']);

  s=slide('02  Implemented system','Official knowledge and source boundaries',5);
  const metrics=[['50','public source documents'],['1,073','searchable passages'],['968','extractive Q&A records']];
  metrics.forEach((m,i)=>{text(s,m[0],72+i*385,235,355,90,64,C.green,true);text(s,m[1],72+i*385,336,350,75,25);});
  text(s,'Public VIT Vellore HTML and PDFs, imported 24 October 2026',72,464,1136,60,29,C.ink,true);
  text(s,'Original URLs and retrieval dates stay visible. Programme and policy-year scope matter.\nQ&A extracts are section records, not 968 independently reviewed FAQs.',72,546,1136,92,25,C.muted);
  notes(s,'35 seconds. Counts come from the recorded official-dataset validation, not a fresh database recount in this artifact task. Ingestion uses allowlisted URLs, heading/page-aware splitting and OCR where needed. Refresh is manual. Official mode excludes the fictional sample corpus. Publication dates may differ from download dates.',['reports/official-dataset.md','knowledge/official/manifest.json','backend/app/import_official.py','backend/app/seed.py']);

  s=slide('03  Short demonstration','Two-minute live demonstration',6,true);
  const steps=[['00:00','Ask','What choices does FFCS give students?'],['00:30','Inspect','Open the citation and original source.'],['01:00','Follow up','What choices does it give me?'],['01:30','Handle a gap','What is my personal attendance percentage today?']];
  steps.forEach((a,i)=>{const y=224+i*101;text(s,a[0],72,y,120,40,26,'#DBE6DD',true);text(s,a[1],230,y,235,40,28,C.white,true);text(s,a[2],495,y,710,70,26,C.white);});
  notes(s,'Demo instructions. Open https://campus-helpdesk-rho.vercel.app before presenting. The backend may need time to wake. Start a new conversation. Ask the FFCS question, open its source, then use the pronoun follow-up in this same conversation. Ask the private attendance question and show the consent offer. Choose No thanks: this demonstration stops before saving a ticket. The exact demo sequence is proposed for the presentation, not a new test result. If a request fails, show the recorded examples on the next slide and label them as recorded. Never claim a failed save succeeded. A full optional staff demonstration requires explicit consent to create one real demo ticket.',['reports/official-live-evaluation.md','reports/official-context-and-consent.md','DEPLOYMENT.md']);

  s=slide('03  Short demonstration','Recorded behavior examples',7);
  row(s,'A','Supported question','FFCS choices: the recorded answer lists course order, time slots and course load.',224);
  row(s,'B','Ambiguous question','“When does the lab open?” returns “Which lab do you mean?”',363);
  row(s,'C','Private information','Personal attendance returns a staff-confirmation offer with no saved ticket.',502);
  notes(s,'30 seconds, or use as the demo fallback. These paraphrase the recorded official live evaluation. They are not screenshots or a fresh live run. The evaluator recorded eight supported responses, two clarifications and two unsupported outcomes. Do not present the examples as proof of universal answer accuracy.',['reports/official-live-evaluation.md']);

  s=slide('04  Evaluation','Verification evidence and its limits',8);
  const results=[['77 backend tests','Current isolated regression suite'],['18 frontend tests','Current UI/API component suite'],['30 / 30 retrieval checks','Expected source family in top eight'],['12 / 12 live checks','Recorded outcome and source-family checks']];
  results.forEach((a,i)=>{const y=221+i*89;text(s,a[0],72,y,470,48,32,C.green,true);text(s,a[1],565,y+4,645,65,27);});
  text(s,'Recorded consent regression: eight turns, one ticket only after confirmation.\nThese checks do not establish universal factual accuracy.',72,593,1136,65,23,C.muted);
  notes(s,'45 seconds. Isolated test counts and production build were rerun during preparation. Retrieval and live model figures come from existing reports, not new paid calls for this presentation. The consent regression intentionally created one demo ticket after affirmative consent. Automatic source-family checks do not verify every sentence. Earlier failed live iterations remain documented.',['reports/official-retrieval.md','reports/official-live-evaluation.md','reports/official-context-and-consent.md','reports/unsupported-citation-fix.md','backend/tests','frontend/src/App.test.tsx']);

  s=slide('04  Evaluation','Implemented safeguards and current limits',9);
  text(s,'Implemented',72,223,515,48,32,C.green,true);
  text(s,'Approved-source retrieval\nCitation-ID validation and bounded repair\nHistory-based follow-up resolution\nMessage-specific ticket confirmation\nVisible service and persistence errors',72,292,535,285,28);
  text(s,'Current limits',694,223,515,48,32,C.green,true);
  text(s,'Bounded conversation memory\nManual source refresh and OCR risk\nNo student identity or private records\nNo staff replies or notifications\nLatest hosted fix verification pending',694,292,515,285,28);
  notes(s,'40 seconds. Citation validity proves provenance, not that every generated claim is entailed. Conversation handles are UUIDs without student authentication, so the prototype is unsuitable for sensitive student records. The unsupported-answer fix passed local checks but its hosted behavior still needs verification after deployment. Viewing the home screen today does not close that gap.',['README.md','reports/official-dataset.md','reports/unsupported-citation-fix.md','DEPLOYMENT.md']);

  s=slide('05  Future work','Proposed next steps',10);
  row(s,'01','Before a campus pilot','Verify hosted flows, review sources with staff, add request limits and retention rules.',224);
  row(s,'02','Identity and communication','Institutional SSO, role-based access, staff replies and student notifications.',363);
  row(s,'03','Knowledge and evaluation','Scheduled refresh, source-change review and a human-labelled answer benchmark.',502);
  notes(s,'35 seconds. All items on this slide are proposed. They are not complete. Private VTOP integration would additionally require institutional approval, scoped access and privacy controls. Avoid promising a timeline without staffing or approval.',['README.md','DEPLOYMENT.md','reports/official-dataset.md']);

  s=slide('05  Close','Project outcome',11,true);
  text(s,'A working prototype for public campus questions,\nwith inspectable sources and consent-based\nstaff routing.',72,243,1136,205,42,C.white);
  text(s,'Next milestone: a verified, staff-reviewed pilot',72,522,1136,60,29,'#DBE6DD');
  text(s,'Questions',72,604,1136,42,26,C.white,true);
  notes(s,'20 seconds. Close by separating the implemented prototype from the future campus pilot. The project demonstrates the complete public-information question path and staff ticket queue. It makes no claim of official VIT endorsement or production readiness.',['README.md','DEPLOYMENT.md']);
}
