import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
const mockFetch=vi.fn();
beforeEach(()=>{vi.stubGlobal('fetch',mockFetch);sessionStorage.clear();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();mockFetch.mockReset();});
function show(path='/'){return render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>);}
function response(data:unknown,ok=true){return {ok,json:async()=>data};}

describe('student workflow',()=>{
  it('keeps a question available after a network failure',async()=>{
    mockFetch.mockRejectedValue(new Error('offline'));
    show();const user=userEvent.setup();
    await user.type(screen.getByLabelText('Ask a campus question'),'Where is SJT 301?');
    await user.click(screen.getByRole('button',{name:'Send question'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach');
    expect(screen.getByLabelText('Ask a campus question')).toHaveValue('Where is SJT 301?');
  });
  it('renders cited answers and successful ticket references',async()=>{
    mockFetch.mockResolvedValueOnce(response({conversation_id:'test',user_message_id:'user-1',outcome:'answered',message:'SJT 301 is on the third floor.',sources:[{id:'faq-01:0',document_id:'faq-01',title:'Finding room SJT 301',heading:'Location',content:'Third floor, Silver Jubilee Tower.'}]}));
    mockFetch.mockResolvedValueOnce(response({ticket_reference:'HD-EXAMPLE'}));
    show();const user=userEvent.setup();
    await user.click(screen.getByRole('button',{name:/Find a classroom/}));
    await user.click(screen.getByRole('button',{name:'Send question'}));
    expect(await screen.findByText('SJT 301 is on the third floor.')).toBeVisible();
    expect(screen.getByRole('button',{name:'Finding room SJT 301'})).toBeVisible();
    await user.click(screen.getByRole('button',{name:/Ask staff about this answer/}));
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('heading',{name:'Raise a ticket for this question?'})).toHaveFocus();
    await user.click(screen.getByRole('button',{name:'No thanks'}));
    expect(screen.getByRole('button',{name:/Ask staff about this answer/})).toHaveFocus();
    await user.click(screen.getByRole('button',{name:/Ask staff about this answer/}));
    await user.click(screen.getByRole('button',{name:'Yes, raise a ticket'}));
    expect(await screen.findByText(/HD-EXAMPLE/)).toBeVisible();
  });
  it('keeps unsupported answers distinct from service errors',async()=>{
    mockFetch.mockResolvedValueOnce(response({conversation_id:'test',user_message_id:'user-1',outcome:'escalated',message:'I could not find that information. Your question was sent to student support.',sources:[],ticket_reference:'HD-SAVED'}));
    show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'weather tomorrow');await user.click(screen.getByRole('button',{name:'Send question'}));
    expect(await screen.findByText('HD-SAVED')).toBeVisible();
    expect(screen.queryByRole('button',{name:/Ask staff about this answer/})).not.toBeInTheDocument();
  });
});
it('searches the knowledge base and filters categories',async()=>{
  mockFetch.mockResolvedValue(response([{id:'1',title:'Robotics lab hours',category:'labs',kind:'faq',content:'Lab hours are 9 to 5.'},{id:'2',title:'Lost ID',category:'procedures',kind:'faq',content:'Report a lost ID.'}]));
  show('/knowledge');const user=userEvent.setup();await screen.findByText('Robotics lab hours');
  await user.click(screen.getByRole('radio',{name:'Labs'}));
  expect(screen.queryByText('Lost ID')).not.toBeInTheDocument();
  await user.type(screen.getByLabelText('Search the knowledge base'),'not-present');
  expect(screen.getByText('No matching sources')).toBeVisible();
  expect(screen.getByRole('textbox',{name:'Search the knowledge base'})).toHaveValue('not-present');
});
it('labels the local source preview when the API is unavailable',async()=>{
  mockFetch.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(response([{id:'1',title:'Sample source',category:'labs',kind:'faq',content:'Example'}]));
  show('/knowledge');expect(await screen.findByText(/Viewing bundled sample sources/)).toBeVisible();
});
it('requires staff sign-in and never displays an invented queue',async()=>{
  mockFetch.mockResolvedValue(response({detail:'Incorrect username or password.'},false));
  show('/staff');const user=userEvent.setup();
  await user.type(screen.getByLabelText('Username'),'staff');await user.type(screen.getByLabelText('Password'),'wrong');await user.click(screen.getByRole('button',{name:'Sign in'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect username');
  expect(screen.queryByText('You’re all caught up.')).not.toBeInTheDocument();
  await waitFor(()=>expect(mockFetch).toHaveBeenCalledTimes(1));
});
it('restores the conversation across navigation and clears it on new conversation',async()=>{
  mockFetch.mockResolvedValueOnce(response({conversation_id:'saved-conversation',user_message_id:'saved-user',outcome:'answered',message:'A saved campus answer.',sources:[]})).mockResolvedValue(response([]));
  show();const user=userEvent.setup();
  await user.type(screen.getByLabelText('Ask a campus question'),'Where is my classroom?');await user.click(screen.getByRole('button',{name:'Send question'}));
  await screen.findByText('A saved campus answer.');
  await user.click(screen.getByRole('link',{name:'Knowledge base'}));
  await user.click(screen.getByRole('link',{name:'Ask a question'}));
  expect(await screen.findByText('A saved campus answer.')).toBeVisible();
  await user.click(screen.getByRole('link',{name:'New conversation'}));
  expect(screen.queryByText('A saved campus answer.')).not.toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'A question about campus?'})).toBeVisible();
});
it('offers a ticket without sending a request until the student confirms',async()=>{
  mockFetch.mockResolvedValueOnce(response({conversation_id:'ticket-conversation',user_message_id:'original-question',outcome:'needs_staff_confirmation',message:'I couldn’t find an answer. Would you like me to raise a ticket?',sources:[],ticket_offer:{message_id:'original-question',query:'Unknown campus policy'}}));
  mockFetch.mockResolvedValueOnce(response({ticket_reference:'HD-CONFIRMED'}));
  show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Unknown campus policy');await user.click(screen.getByRole('button',{name:'Send question'}));
  expect(await screen.findByRole('button',{name:'Yes, raise a ticket'})).toBeVisible();
  expect(screen.getByRole('button',{name:'No thanks'})).toBeVisible();
  expect(mockFetch).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole('button',{name:'Yes, raise a ticket'}));
  expect(await screen.findByText('HD-CONFIRMED')).toBeVisible();
  const request=mockFetch.mock.calls[1];
  expect(request[0]).toBe('/api/conversations/ticket-conversation/escalate');
  expect(JSON.parse(request[1].body)).toEqual({message_id:'original-question',confirmed:true});
});
it('declines a ticket without calling the escalation endpoint',async()=>{
  mockFetch.mockResolvedValueOnce(response({conversation_id:'ticket-conversation',user_message_id:'original-question',outcome:'needs_staff_confirmation',message:'Would you like a ticket?',sources:[],ticket_offer:{message_id:'original-question',query:'Unknown policy'}}));
  mockFetch.mockResolvedValueOnce(response({conversation_id:'ticket-conversation',user_message_id:'decline-message',outcome:'conversation',message:'Okay, I won’t raise a ticket.',sources:[]}));
  show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Unknown policy');await user.click(screen.getByRole('button',{name:'Send question'}));
  await user.click(await screen.findByRole('button',{name:'No thanks'}));
  expect(await screen.findByText('Okay, I won’t raise a ticket.')).toBeVisible();
  expect(mockFetch.mock.calls.every(call=>call[0]==='/api/chat')).toBe(true);
  expect(JSON.parse(mockFetch.mock.calls[1][1].body)).toMatchObject({message:'No thanks',conversation_id:'ticket-conversation'});
});
it('sends the same conversation ID for a six-word follow-up',async()=>{
  mockFetch.mockResolvedValueOnce(response({conversation_id:'context-id',user_message_id:'first-user',outcome:'answered',message:'Apply for an ID replacement. The fee is ₹200.',sources:[]}));
  mockFetch.mockResolvedValueOnce(response({conversation_id:'context-id',user_message_id:'next-user',outcome:'answered',message:'The fee is ₹200.',sources:[]}));
  show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'How do I replace a lost student ID?');await user.click(screen.getByRole('button',{name:'Send question'}));
  await screen.findByText('Apply for an ID replacement. The fee is ₹200.');
  await user.type(screen.getByLabelText('Ask a campus question'),'so how much do i pay?');await user.click(screen.getByRole('button',{name:'Send question'}));
  expect(await screen.findByText('The fee is ₹200.')).toBeVisible();
  expect(JSON.parse(mockFetch.mock.calls[1][1].body)).toMatchObject({message:'so how much do i pay?',conversation_id:'context-id'});
});
it('keeps ticket consent available after a save failure and never claims success',async()=>{
  mockFetch.mockResolvedValueOnce(response({conversation_id:'conversation',user_message_id:'question-id',outcome:'needs_staff_confirmation',message:'Would you like a ticket?',sources:[],ticket_offer:{message_id:'question-id',query:'Missing policy'}}));
  mockFetch.mockRejectedValueOnce(new Error('network failure'));
  show();const user=userEvent.setup();await user.type(screen.getByLabelText('Ask a campus question'),'Missing policy');await user.click(screen.getByRole('button',{name:'Send question'}));
  await user.click(await screen.findByRole('button',{name:'Yes, raise a ticket'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach');
  expect(screen.getByRole('button',{name:'Yes, raise a ticket'})).toBeEnabled();
  expect(screen.queryByText(/Ticket raised/)).not.toBeInTheDocument();
});

it('opens a source in a keyboard-dismissible dialog and returns focus',async()=>{
  mockFetch.mockResolvedValue(response([{id:'1',title:'Robotics lab hours',category:'labs',kind:'faq',content:'Lab hours are 9 to 5.'}]));
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
