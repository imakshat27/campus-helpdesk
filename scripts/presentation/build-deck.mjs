import fs from 'node:fs/promises';

// Presentation status incorporates the team's completion confirmation of 25 Oct.
export async function buildDeck(presentation, root) {
  presentation.slides.keep([]);
  const C={paper:'#F6F3ED',ink:'#142B35',muted:'#5F6D72',teal:'#176B64',light:'#CFE5DF',white:'#FFFFFF',ochre:'#AD622F'};
  presentation.theme.defaultFont='Arial';
  function t(s,value,x,y,w,h,size=28,color=C.ink,bold=false){
    const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    sh.text=value;sh.text.style={typeface:'Arial',fontSize:size,color,bold};return sh;
  }
  function slide(section,title,n,dark=false){
    const s=presentation.slides.add({width:1280,height:720});s.background.fill=dark?C.ink:C.paper;
    t(s,section.toUpperCase(),64,38,1050,28,18,dark?C.light:C.teal,true);
    if(title)t(s,title,64,100,1152,126,49,dark?C.white:C.ink,true);
    t(s,'CAMPUS HELPDESK',64,675,500,22,13,dark?C.light:C.muted);
    t(s,String(n).padStart(2,'0'),1150,669,66,28,20,dark?C.light:C.teal,true);return s;
  }
  function item(s,title,body,x,y,w=520,dark=false){t(s,title,x,y,w,70,31,dark?C.white:C.teal,true);t(s,body,x,y+77,w,115,27,dark?C.light:C.muted);}
  function notes(s,body,refs=[]){s.speakerNotes.text=body+'\n\nEvidence: '+refs.join(', ')+'. Presentation date: 25 October 2026. Two-account login, saved conversations and live staff chat are complete and verified according to the project owner’s confirmation on 25 October 2026. This document revision does not claim a new independent test of the teammate’s build.';}

  let s=slide('VIT Vellore  /  Project presentation','',1,true);
  t(s,'Campus\nHelpdesk',64,133,850,260,96,C.white,true);
  t(s,'AI answers with sources.\nStaff support in the same conversation.',70,450,1020,122,35,C.light);
  t(s,'25 October 2026',70,603,1000,42,25,C.white);
  notes(s,'Opening, 15 seconds. Introduce an independent academic project combining source-backed AI and human support. Use this order: problem, idea, implementation, short demonstration, limitations, future scope. Suggested duration is 7 to 8 minutes including the demo.',['README.md','Project owner completion confirmation']);

  s=slide('01  Problem','Finding the right campus information',2);
  t(s,'A student has\na question.',64,263,470,170,58,C.ink,true);
  t(s,'Hostel booking. Library rules.\nAcademic procedures.',64,475,470,110,29,C.muted);
  item(s,'Information is spread out','Relevant details sit across university pages, policy PDFs and different offices.',660,252,535);
  item(s,'Some answers need staff','Unclear details and personal requests need a human response.',660,461,535);
  notes(s,'30 seconds. Describe the information-discovery problem as the motivation, not as a measured survey result. Public source search helps students find guidance, and staff handle cases the collection cannot answer.',['README.md','reports/official-dataset.md']);

  s=slide('02  Idea','One place for campus questions',3,true);
  t(s,'Ask naturally.\nCheck the source.\nContinue with staff.',64,246,1090,236,57,C.white,true);
  t(s,'The student confirms before a conversation goes to staff.',70,567,1100,64,28,C.light);
  notes(s,'25 seconds. Explain the idea before the technology: a question interface with inspectable university evidence and a consent-based path into live human support. This is the functional project outcome confirmed by the team. No measured response-time or workload improvement is claimed.',['README.md','Project owner completion confirmation']);

  s=slide('03  How it works','The student-to-staff journey',4);
  const steps=[['01','Ask','Sign in and ask a campus question.'],['02','Get an AI answer','Retrieve public sources and show citations.'],['03','Confirm a handoff','Save the request and pause AI replies.'],['04','Chat with staff','Staff takes over, replies and resolves the chat.']];
  steps.forEach((a,i)=>{let y=242+i*98;t(s,a[0],64,y,72,46,30,C.ochre,true);t(s,a[1],168,y,310,48,30,C.ink,true);t(s,a[2],535,y,670,76,28,C.muted);});
  notes(s,'40 seconds. Distinguish an AI answer from a staff reply. Staff only sees confirmed handoffs. While the student waits and while staff is active, AI remains paused. Resolution closes the composer, with explicit reopening or a separate new AI conversation available.',['User-supplied two-account and live-chat specification','Project owner completion confirmation']);

  s=slide('04  Implementation','The system behind the conversation',5);
  item(s,'Interface','React and TypeScript\nStudent chat and staff workspace',64,239);
  item(s,'Application','FastAPI and Python\nLogin, conversations and handoff logic',681,239);
  item(s,'Knowledge and storage','Neon PostgreSQL with pgvector\nSources, history, tickets and vector search',64,448);
  item(s,'AI and live delivery','OpenRouter for grounded answers\nWebSockets for message and status updates',681,448);
  notes(s,'35 seconds. Keep the explanation at component level. Retrieval-augmented generation finds relevant source passages before model generation. HTTP handles authenticated sends and WebSockets carry committed updates. Neon remains authoritative. These describe the supplied design and the team-confirmed completed extension, not independently reviewed endpoint names.',['README.md','User-supplied specification','Project owner completion confirmation']);

  s=slide('04  Implementation','Source-backed AI assistance',6);
  t(s,'Public VIT Vellore\ninformation',64,250,800,148,51,C.ink,true);
  t(s,'Academics, library, hostels and student services',68,427,770,88,30,C.teal,true);
  t(s,'Inspect the passage and original source.\nFollow up without repeating the topic.',68,550,780,92,28,C.muted);
  const b=await fs.readFile(root+'/scripts/presentation/assets/helpdesk-home.png');
  s.images.add({dataUrl:'data:image/png;base64,'+b.toString('base64'),contentType:'image/png',alt:'Actual helpdesk question screen captured 25 October 2026 before account-workflow updates',fit:'contain',position:{left:950,top:221,width:255,height:412}});
  notes(s,'30 seconds. The corpus uses public Vellore pages and PDFs. Cite actual passages, preserve policy dates and programme scope, and use stored history for follow-ups. Screenshot is an earlier actual question-screen capture, not evidence of the updated account or staff-chat screens. Do not treat retrieval dates as a guarantee of current policy.',['knowledge/official/manifest.json','reports/official-dataset.md','backend/app/retrieval.py']);

  s=slide('04  Implementation  /  Complete','Two accounts, with saved conversations',7);
  t(s,'Student',64,243,500,55,40,C.teal,true);
  t(s,'Ask the AI assistant\nStart or resume a conversation\nReturn to history after signing in',64,331,535,175,30);
  t(s,'Staff',681,243,500,55,40,C.teal,true);
  t(s,'Open confirmed support requests\nRead the conversation context\nTake over and reply live',681,331,535,175,30);
  t(s,'One shared login screen opens the workspace for each role.',64,585,1150,55,28,C.muted);
  notes(s,'35 seconds. Exactly two fixed accounts, one student and one staff. Login sessions and conversations are distinct. Students see their own chats, while staff accesses confirmed handoffs. This feature set is complete and verified per the owner. Do not describe it as proposed. No registration or password-reset system is included in this version.',['User-supplied specification','Project owner completion confirmation']);

  s=slide('05  Demonstration','A short end-to-end demonstration',8,true);
  const demo=[['01','Ask and inspect','Student asks an FFCS question and opens its source.'],['02','Resume a saved chat','Sign back in and reopen the conversation history.'],['03','Confirm staff help','Request a handoff and show the waiting state.'],['04','Reply as staff','Staff starts chat, sends a reply, then resolves it.']];
  demo.forEach((a,i)=>{let y=239+i*98;t(s,a[0],64,y,65,45,29,C.light,true);t(s,a[1],168,y,322,50,29,C.white,true);t(s,a[2],540,y,660,79,27,C.light);});
  notes(s,'About 2 to 3 minutes. Use separate student and staff browser sessions, prepared before speaking. Never project credentials. Student asks “What choices does FFCS give students?” and opens a citation. Show a saved chat after re-login, using prepared history if time is short. Student explicitly confirms a staff handoff for the selected question, creating or reusing a real demo ticket. Verify AI pauses and the waiting state appears. In the staff session select Start chat, send a brief real reply and show it arriving for the student. Resolve and show the closed composer. This is a demo runbook, not a claim that this exact sequence ran during artifact preparation. If unavailable, describe the team-verified flow honestly rather than simulating successful replies.',['User-supplied specification','Project owner completion confirmation']);

  s=slide('06  Scope and limitations','Public guidance with human support',9);
  item(s,'What the project supports','Public campus questions\nSaved conversation history\nLive staff support after consent',64,250,535);
  item(s,'What still needs care','Private VTOP data remains unavailable\nPolicies vary by programme and year\nStaff availability affects waiting time',681,250,535);
  t(s,'Source inspection and staff review remain important for critical decisions.',64,582,1150,60,28,C.muted);
  notes(s,'30 seconds. Two fixed accounts are a demonstration scope, not an institution-wide account system. Public source grounding does not make every generated claim correct. OCR and stale policy risks remain. Multi-worker real-time scaling and institution-level identity are future rollout concerns.',['reports/official-dataset.md','User-supplied specification','Project owner completion confirmation']);

  s=slide('07  Future scope','Beyond the two-account version',10);
  item(s,'Broader campus rollout','More users and departments\nScalable staff routing and deployment',64,241);
  item(s,'Source maintenance','Scheduled refresh of official material\nReview changes before publishing',681,241);
  item(s,'University integration','Institutional sign-in\nApproved, scoped access to university systems',64,450);
  item(s,'Institutional readiness','Privacy and retention policies\nStaff review and wider accessibility checks',681,450);
  notes(s,'35 seconds. Only this slide describes future work. The two accounts, history and live chat are already complete per owner confirmation. Broader rollout, scheduled source refresh and institutional integration are beyond that delivered scope. Private-system access requires institutional authorization and privacy controls. No delivery dates are promised.',['Project owner future-scope instruction','README.md']);

  s=slide('08  Conclusion','AI guidance with a human continuation',11,true);
  t(s,'Implemented',64,244,330,55,32,C.light,true);
  t(s,'Cited answers, saved chats\nand live staff support',430,244,775,148,46,C.white,true);
  t(s,'Future scope',64,462,330,55,32,C.light,true);
  t(s,'Broader rollout and\nuniversity integration',430,462,775,130,40,C.white);
  t(s,'Questions',64,617,1000,40,27,C.light);
  notes(s,'15 seconds. Close with the clear split: working source-backed AI, account history and live staff continuation, followed by future institutional rollout. The project is an independent academic prototype, without a claim of university endorsement.',['Project owner completion confirmation','Project owner future-scope instruction']);
}
