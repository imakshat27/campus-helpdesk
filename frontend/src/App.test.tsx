import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { AccountContext } from './components/AccessGate';
const mockFetch=vi.fn();
beforeEach(()=>{vi.stubGlobal('fetch',mockFetch);sessionStorage.clear();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();mockFetch.mockReset();});
function show(path='/',role:'student'|'staff'='student'){return render(<AccountContext.Provider value={{id:'account',username:role,role}}><MemoryRouter initialEntries={[path]}><App/></MemoryRouter></AccountContext.Provider>);}
function response(data:unknown,ok=true){return {ok,status:ok?200:503,json:async()=>data};}
function chatServer(){
 const data={id:'saved-chat',conversation_id:'saved-chat',title:'Saved question',state:'ai',ticket_reference:'',messages:[] as Array<Record<string,unknown>>};
 let failSend=false,failEscalate=false;
 const request=async(url:string,options:RequestInit={})=>{
   const body=options.body?JSON.parse(String(options.body)):{};
   if(url==='/api/conversations' && options.method==='POST')return response({id:data.id});
   if(url==='/api/conversations')return response(data.messages.length?[{...data,messages:undefined}]:[]);
   if(url==='/api/knowledge')return response([]);
   if(url.endsWith('/escalate')){
     if(failEscalate)throw new Error('offline');
     data.state='waiting_for_staff';data.ticket_reference='HD-CONFIRMED';return response({ticket_reference:'HD-CONFIRMED'});
   }
   if(url.endsWith('/accept')){data.state='staff_active';return response(structuredClone(data));}
   if(url.endsWith('/reopen')){data.state='waiting_for_staff';return response(structuredClone(data));}
   if(url.endsWith('/messages')){
     if(failSend)throw new Error('offline');
     const id='question-'+data.messages.length;
     data.messages.push({id,role:'user',content:body.message,sequence:data.messages.length+1,created_at:'2026-10-25T10:00:00Z'});
     if(data.state==='ai'){
       const missing=body.message.includes('Unknown');
       data.messages.push({id:'answer-'+id,role:'assistant',content:body.message==='No thanks'?'Okay, I won’t raise a ticket.':missing?'Would you like a ticket?':'A saved campus answer.',outcome:missing?'needs_staff_confirmation':'answered',user_message_id:id,sources:[],ticket_offer:missing?{message_id:id,query:body.message}:null,sequence:data.messages.length+1});
     }
     return response(structuredClone(data));
   }
   if(url.startsWith('/api/conversations/'))return response(structuredClone(data));
   if(url.startsWith('/api/staff/tickets'))return response([]);
   throw new Error('Unexpected URL '+url);
 };
 mockFetch.mockImplementation(request);
 return {data,failSend:()=>{failSend=true;},failEscalate:()=>{failEscalate=true;}};
}

it('retains the draft after a failed send and reuses its request ID on retry',async()=>{
 const server=chatServer();server.failSend();show();const user=userEvent.setup();
 await user.type(screen.getByLabelText('Ask a campus question'),'Where is my classroom?');await user.click(screen.getByRole('button',{name:'Send question'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach');expect(screen.getByLabelText('Ask a campus question')).toHaveValue('Where is my classroom?');
 await user.click(screen.getByRole('button',{name:'Send question'}));
 await waitFor(()=>expect(mockFetch.mock.calls.filter(c=>String(c[0]).endsWith('/messages'))).toHaveLength(2));
 const sends=mockFetch.mock.calls.filter(c=>String(c[0]).endsWith('/messages'));
 expect(JSON.parse(sends[0][1].body).client_request_id).toBe(JSON.parse(sends[1][1].body).client_request_id);
});

it('loads saved history from the server and restores it after navigation',async()=>{
 chatServer();show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Where is my classroom?');await user.click(screen.getByRole('button',{name:'Send question'}));
 await screen.findByText('A saved campus answer.');await user.click(screen.getByRole('link',{name:'Knowledge base'}));await user.click(await screen.findByRole('link',{name:'Saved question'}));
 expect(await screen.findByText('A saved campus answer.')).toBeVisible();await user.click(screen.getByRole('link',{name:'New conversation'}));
 expect(await screen.findByRole('heading',{name:'A question about campus?'})).toBeVisible();expect(screen.queryByText('A saved campus answer.')).not.toBeInTheDocument();
});

it('waits for explicit consent then displays the staff waiting state',async()=>{
 chatServer();show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Unknown campus policy');await user.click(screen.getByRole('button',{name:'Send question'}));
 await user.click(await screen.findByRole('button',{name:'Yes, raise a ticket'}));
 expect(await screen.findByText('HD-CONFIRMED')).toBeVisible();expect(screen.getByText(/Waiting for staff/)).toBeVisible();
 const call=mockFetch.mock.calls.find(c=>String(c[0]).endsWith('/escalate'))!;expect(JSON.parse(call[1].body)).toEqual({message_id:'question-0',confirmed:true});
 expect(screen.getByRole('button',{name:'Send message'})).toBeDisabled();
 await user.type(screen.getByLabelText('Message student support'),'Extra detail');expect(screen.getByRole('button',{name:'Send message'})).toBeEnabled();
});

it('retains the offer when a ticket save fails',async()=>{
 const server=chatServer();server.failEscalate();show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Unknown policy');await user.click(screen.getByRole('button',{name:'Send question'}));await user.click(await screen.findByRole('button',{name:'Yes, raise a ticket'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach');expect(screen.getByRole('button',{name:'Yes, raise a ticket'})).toBeEnabled();expect(screen.queryByText('HD-CONFIRMED')).not.toBeInTheDocument();
});

it('declines without calling escalation',async()=>{
 chatServer();show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Unknown policy');await user.click(screen.getByRole('button',{name:'Send question'}));await user.click(await screen.findByRole('button',{name:'No thanks'}));
 expect(await screen.findByText('Okay, I won’t raise a ticket.')).toBeVisible();expect(mockFetch.mock.calls.some(c=>String(c[0]).endsWith('/escalate'))).toBe(false);
});

it('requires staff acceptance before replying and labels staff separately',async()=>{
 const server=chatServer();server.data.state='waiting_for_staff';server.data.messages.push({id:'staff-msg',role:'staff',content:'A real staff reply',sequence:1});show('/staff/saved-chat','staff');const user=userEvent.setup();
 expect(await screen.findByText('A real staff reply')).toBeVisible();expect(screen.getByText('Student support · Staff')).toBeVisible();expect(screen.getByLabelText('Message student')).toBeDisabled();
 await user.click(screen.getByRole('button',{name:'Start chat'}));expect(await screen.findByLabelText('Message student')).toBeEnabled();
});

it('closes resolved chats and permits explicit student reopening',async()=>{
 const server=chatServer();server.data.state='resolved';show('/conversations/saved-chat');const user=userEvent.setup();
 await user.click(await screen.findByRole('button',{name:'Reopen conversation'}));expect(await screen.findByText(/Waiting for staff/)).toBeVisible();
});

it('keeps drafts across navigation and clears new-conversation drafts explicitly',async()=>{
 chatServer();show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'My unsent question');await user.click(screen.getByRole('link',{name:'Knowledge base'}));await user.click(screen.getByRole('link',{name:'Ask a question'}));
 expect(screen.getByLabelText('Ask a campus question')).toHaveValue('My unsent question');await user.click(screen.getByRole('link',{name:'New conversation'}));expect(screen.getByLabelText('Ask a campus question')).toHaveValue('');
});

it('searches the knowledge base and filters categories',async()=>{
  mockFetch.mockImplementation((url:string)=>Promise.resolve(response(url==='/api/conversations'?[]:[{id:'1',title:'Robotics lab hours',category:'labs',kind:'faq',content:'Lab hours are 9 to 5.'},{id:'2',title:'Lost ID',category:'procedures',kind:'faq',content:'Report a lost ID.'}])));
  show('/knowledge');const user=userEvent.setup();await screen.findByText('Robotics lab hours');
  await user.click(screen.getByRole('radio',{name:'Labs'}));
  expect(screen.queryByText('Lost ID')).not.toBeInTheDocument();
  await user.type(screen.getByLabelText('Search the knowledge base'),'not-present');
  expect(screen.getByText('No matching sources')).toBeVisible();
  expect(screen.getByRole('textbox',{name:'Search the knowledge base'})).toHaveValue('not-present');
});
it('does not substitute fictional sample sources when the official API fails',async()=>{
 mockFetch.mockRejectedValueOnce(new Error('offline'));
 show('/knowledge');expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded');
 expect(mockFetch.mock.calls.some(c=>c[0]==='/api/knowledge')).toBe(true);
 expect(screen.queryByText(/bundled sample/)).not.toBeInTheDocument();
});
it('opens a source in a keyboard-dismissible dialog and returns focus',async()=>{
  mockFetch.mockImplementation((url:string)=>Promise.resolve(response(url==='/api/conversations'?[]:[{id:'1',title:'Robotics lab hours',category:'labs',kind:'faq',content:'Lab hours are 9 to 5.'}])));
  show('/knowledge');const user=userEvent.setup();
  const source=await screen.findByRole('button',{name:/Robotics lab hours/});
  await user.click(source);
  expect(screen.getByRole('dialog',{name:'Robotics lab hours'})).toBeVisible();
  expect(screen.getByRole('button',{name:'Close source'})).toHaveFocus();
  await user.keyboard('{Escape}');
  await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(source).toHaveFocus();
});

it('opens mobile navigation and restores the trigger after Escape',async()=>{
  const previousWidth=window.innerWidth;
  Object.defineProperty(window,'innerWidth',{value:375,writable:true,configurable:true});
  try {
    show();const user=userEvent.setup();
    const trigger=screen.getByRole('button',{name:'Open navigation'});
    await user.click(trigger);
    expect(screen.getByRole('dialog',{name:'Sidebar'})).toBeVisible();
    expect(screen.getByRole('button',{name:'Close navigation'})).toHaveFocus();
    await user.keyboard('{Escape}');
    await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  } finally { Object.defineProperty(window,'innerWidth',{value:previousWidth,writable:true,configurable:true}); }
});

it('shows official provenance and readable policy tables',async()=>{
 mockFetch.mockImplementation((url:string)=>Promise.resolve(response(url==='/api/conversations'?[]:[{id:'official',title:'Library policy',category:'library',kind:'official',content:'## Borrowing\n\n| Type | Books |\n|---|---|\n| UG | 5 |',source_url:'https://vit.ac.in/academics/library',campus:'Vellore',retrieved_at:'2026-10-24T12:00:00Z'}])));
 show('/knowledge');const user=userEvent.setup();await user.click(await screen.findByRole('button',{name:/Library policy/}));
 expect(screen.getByRole('link',{name:/Open original VIT source/})).toHaveAttribute('href','https://vit.ac.in/academics/library');
 expect(await screen.findByRole('table')).toHaveTextContent('UG');
 expect(screen.getByRole('dialog')).toHaveTextContent('Vellore');
});
