import fs from 'node:fs/promises';

// Audience-facing project story. Development verification stays in the report.
export async function buildDeck(presentation, root) {
  presentation.slides.keep([]);
  const C={paper:'#F8F7F4',ink:'#232B27',muted:'#606861',green:'#294F40',white:'#FFFFFF',light:'#DBE6DD'};
  presentation.theme.defaultFont='Arial';
  function text(s,value,x,y,w,h,size=28,color=C.ink,bold=false){
    const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    sh.text=value;sh.text.style={typeface:'Arial',fontSize:size,color,bold};return sh;
  }
  function slide(section,title,n,dark=false){
    const s=presentation.slides.add({width:1280,height:720});s.background.fill=dark?C.green:C.paper;
    text(s,section.toUpperCase(),72,38,1100,28,18,dark?C.light:C.green,true);
    text(s,title,72,100,1136,115,46,dark?C.white:C.ink,true);
    text(s,`CAMPUS HELPDESK     /     ${String(n).padStart(2,'0')}`,72,674,1100,22,14,dark?C.light:C.muted);return s;
  }
  function row(s,num,title,body,y,dark=false){
    text(s,num,72,y,65,45,28,dark?C.light:C.green,true);
    text(s,title,158,y,1030,45,30,dark?C.white:C.ink,true);
    text(s,body,158,y+49,1030,83,27,dark?C.light:C.muted);
  }
  function notes(s,body,refs=[]){s.speakerNotes.text=body+'\n\nEvidence: '+refs.join(', ')+'. Prepared 25 October 2026 for 26 October 2026. Planned work comes from the user-provided “Two-account login and persistent live chat” specification and is not implemented.';}

  let s=slide('Project presentation','Campus Helpdesk',1,true);
  text(s,'An AI helpdesk for\ncampus questions',72,250,1136,150,55,C.white);
  text(s,'VIT Vellore',72,465,1100,50,30,C.light);
  text(s,'26 October 2026',72,546,1100,40,25,C.light);
  notes(s,'15 seconds. Introduce the project as an independent academic prototype. The story is problem, idea, working implementation, demonstration, limitations and the planned next version. Suggested duration: 7 to 8 minutes including a short demo.',['README.md']);

  s=slide('01  Problem','Finding the right campus information',2);
  text(s,'“Where do I find the answer?”',72,232,1136,80,43,C.green,true);
  row(s,'01','Information is spread out','Students search across university pages, policy PDFs and different offices.',346);
  row(s,'02','Some questions need a person','An unclear or unpublished detail still needs staff confirmation.',502);
  notes(s,'30 seconds. Use hostel booking, library rules or transcript procedures as familiar examples. Describe the problem as project motivation, not a measured survey result. A conversational interface can help discovery, while staff remain necessary for information outside the public collection.',['README.md','reports/official-dataset.md']);

  s=slide('02  Idea','One place to ask for campus help',3,true);
  text(s,'Ask a question in everyday language.\nRead an answer with its source.\nChoose staff help when needed.',72,245,1136,235,43,C.white);
  text(s,'The student decides when a question goes to staff.',72,555,1136,58,29,C.light);
  notes(s,'30 seconds. Introduce the solution before technology. The goal is to make public information easier to find and inspect, with a clear route for unanswered questions. These are design objectives, not measured time-saving claims. Staff handoff currently creates a queue ticket. Live staff messaging belongs to the planned version.',['README.md','backend/app/main.py']);

  s=slide('03  Approach','How a question becomes an answer',4);
  const flow=[['01','Understand','Use the question and its conversation context.'],['02','Find evidence','Search approved VIT Vellore source passages.'],['03','Answer','Generate a response and attach supporting sources.'],['04','Handle gaps','Ask for clarification or offer a ticket with consent.']];
  flow.forEach((a,i)=>{const y=228+i*100;text(s,a[0],72,y,65,40,28,C.green,true);text(s,a[1],170,y,280,42,30,C.ink,true);text(s,a[2],490,y,720,75,27,C.muted);});
  notes(s,'40 seconds. Explain retrieval-augmented generation, or RAG: retrieve relevant university text first, then generate from those passages. Follow-ups use stored history. Cite source IDs only when they match supplied passages. A valid citation establishes provenance, but a reader should still check critical details.',['backend/app/retrieval.py','backend/app/llm.py','backend/app/main.py']);

  s=slide('04  Implementation','Technology behind the prototype',5);
  const parts=[['React + TypeScript','Chat, source browser and staff workspace',72,234],['FastAPI + Python','Conversation logic and ticket handling',692,234],['Neon PostgreSQL + pgvector','Stored sources, vector search and chat data',72,428],['OpenRouter','AI responses grounded in retrieved text',692,428]];
  parts.forEach(([a,b,x,y])=>{text(s,a,x,y,510,85,33,C.green,true);text(s,b,x,y+91,510,100,28,C.muted);});
  notes(s,'35 seconds. Keep this at component level. The React frontend runs on Vercel and the FastAPI backend uses Render deployment configuration. Sentence Transformers generates embeddings for pgvector search. Alembic manages database migrations. Secrets stay on the backend. Avoid reading configuration commands or development test counts aloud.',['README.md','DEPLOYMENT.md','backend/app/models.py']);

  s=slide('04  Implementation','What works today',6);
  text(s,'Student questions',72,230,760,44,32,C.green,true);
  text(s,'AI answers with inspectable sources\nFollow-up questions in the same conversation\nSearchable public VIT Vellore information',72,295,775,150,29);
  text(s,'Staff support',72,487,760,44,32,C.green,true);
  text(s,'Confirmed tickets in a protected staff queue\nReview context, resolve and reopen tickets',72,551,785,86,29);
  const b=await fs.readFile(root+'/scripts/presentation/assets/helpdesk-home.png');
  s.images.add({dataUrl:'data:image/png;base64,'+b.toString('base64'),contentType:'image/png',alt:'Actual Campus Helpdesk chat home captured 25 October 2026',fit:'contain',position:{left:941,top:215,width:245,height:425}});
  notes(s,'40 seconds. Everything on this slide is implemented. The current access model is a shared private review password with a signed session, plus separate staff authentication. Individual student/staff accounts and saved-history navigation across logins are planned. Database conversation persistence already exists, but it is not the same as an account-based history/resume feature. Screenshot shows the actual chat home captured earlier on 25 October 2026, before the newer review access gate.',['README.md','frontend/src/App.tsx','backend/app/access.py','backend/app/main.py']);

  s=slide('05  Demonstration','A short walkthrough',7,true);
  row(s,'01','Ask and inspect','“What choices does FFCS give students?” Open its source.',225,true);
  row(s,'02','Continue the conversation','“What choices does it give me?” Keep the same topic.',371,true);
  row(s,'03','Show an unanswered question','Ask for personal attendance, then show the ticket-consent offer.',517,true);
  notes(s,'About 2 minutes. Open https://campus-helpdesk-rho.vercel.app and sign in through the existing review gate before presenting. Never project credentials. Ask the exact FFCS question, inspect a citation, then ask the pronoun follow-up. Ask “What is my personal attendance percentage today?” Show the offer, then select No thanks so the default demo saves no ticket. A staff-queue extension requires explicitly confirming a real demo ticket. Do not demonstrate two-account login or live staff replies as implemented. If the live service is unavailable, describe recorded examples from the official live evaluation and label them as recorded. The FFCS result lists course order, time slots and course load. The attendance query returns needs_staff_confirmation without a saved ticket. The complete proposed demo sequence has not been rerun for this revision.',['reports/official-live-evaluation.md','reports/official-context-and-consent.md','DEPLOYMENT.md']);

  s=slide('06  Current scope','What the current version can cover',8);
  text(s,'Public campus information',72,239,520,50,33,C.green,true);
  text(s,'Academics and library services\nHostel information and procedures\nStudent welfare and public contacts',72,316,540,180,29);
  text(s,'Current limitations',692,239,520,50,33,C.green,true);
  text(s,'No private VTOP records or live availability\nNo personal account history across logins\nNo live replies from staff yet',692,316,520,200,29);
  text(s,'Policy dates and programme scope still need attention.',72,580,1136,55,27,C.muted);
  notes(s,'35 seconds. This is an independent public-information prototype. The sources are public VIT Vellore material, and dated policies must retain their programme and year restrictions. Generated answers still need source review for critical decisions. Backend persistence exists, but the account-based resume workflow in the supplied plan does not. Current handoff saves an internal ticket rather than opening a live staff conversation. Full hosted verification of the latest unsupported-response fix remains pending in the project records.',['README.md','reports/official-dataset.md','reports/unsupported-citation-fix.md']);

  s=slide('07  Future scope  /  Proposed','Two accounts and saved conversations',9);
  row(s,'01','One student account and one staff account','A shared login opens the workspace for each role.',225);
  row(s,'02','History that survives sign-out','Start a new conversation or resume an earlier one after logging in.',371);
  row(s,'03','Access tied to the account','Students see their own chats. Staff see confirmed handoffs.',517);
  notes(s,'40 seconds. This entire slide describes future work from the user-provided plan, not current functionality. Exactly two fixed accounts will use the existing React/FastAPI/Neon stack. Proposed database users use Argon2 password hashes, revocable eight-hour sessions and an opaque cookie. There is no registration, password-reset or account-management feature in this phase. Preserve existing official retrieval, consent and request limits. Planned stages start with login, followed by saved conversations and handoff.',['User-provided specification: Two-account login and persistent live chat, 25 October 2026']);

  s=slide('07  Future scope  /  Proposed','Live staff chat after a confirmed handoff',10);
  const stages=[['01','AI assistance','The assistant answers until the student confirms a handoff.'],['02','Waiting for staff','Save the request and pause AI replies.'],['03','Staff conversation','Staff selects Start chat. Both accounts exchange messages live.'],['04','Resolution','Close the chat, with an option to reopen or start a new AI chat.']];
  stages.forEach((a,i)=>{const y=228+i*100;text(s,a[0],72,y,65,40,28,C.green,true);text(s,a[1],170,y,290,47,29,C.ink,true);text(s,a[2],495,y,710,78,26,C.muted);});
  notes(s,'45 seconds. This is proposed, not implemented or demonstrated today. Conversation states are ai, waiting_for_staff, staff_active and resolved. A confirmed handoff creates or reuses one active ticket per conversation and keeps the exact originating question ID. Staff replies receive distinct labels. The plan uses authenticated HTTP for sends and WebSockets for committed messages/status updates. Save first, broadcast second, and recover from reconnects using authoritative Neon history with duplicate prevention. Keep AI paused while waiting and during staff chat. The third planned delivery stage is real-time chat. One backend worker is the initial design. Token streaming, typing indicators, attachments and read receipts are outside this phase.',['User-provided specification: Two-account login and persistent live chat, 25 October 2026']);

  s=slide('08  Conclusion','Campus support with a clear next step',11,true);
  text(s,'Today',72,235,230,50,31,C.light,true);
  text(s,'Source-backed answers and\nconsent-based staff tickets',355,235,835,135,43,C.white);
  text(s,'Next',72,435,230,50,31,C.light,true);
  text(s,'Account-based history and\nlive conversations with staff',355,435,835,135,43,C.white);
  text(s,'Questions',72,612,1136,40,27,C.light);
  notes(s,'20 seconds. Close on the distinction between the working prototype and the planned extension. Today the project helps discover public campus information and creates staff tickets only with consent. The next version adds two role-specific accounts, cross-login history and live human takeover. No claims of official endorsement, measured workload reductions or completed future features.',['README.md','User-provided specification: Two-account login and persistent live chat, 25 October 2026']);
}
