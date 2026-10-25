import { useEffect, useLayoutEffect, useRef, useState, lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { NavLink, Route, Routes, useLocation, Navigate, useNavigate, useParams } from 'react-router-dom';
import { ArrowDown, ArrowRight, ArrowUp, BookOpen, CheckCircle2, ChevronRight, FileText, Headphones, HelpCircle, Inbox, LibraryBig, LoaderCircle, MapPin, MessageSquare, Plus, Search, ShieldCheck, SquareArrowOutUpRight, Ticket as TicketIcon, Wifi, Wrench, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog as UiDialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose, DialogFooter } from '@/components/ui/dialog';
import { SidebarProvider, Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarInset, SidebarTrigger, useSidebar } from '@/components/ui/sidebar';
import { api, conversationChanged } from './api';
import { clearAccess } from './access';
import { useAccount } from './components/AccessGate';
import { useLiveEvents } from './hooks/use-live-events';
const SourceContent=lazy(()=>import('./components/SourceContent'));
import type { Knowledge, Source, Ticket, TicketOffer, ConversationSummary, ConversationDetail, ConversationState } from './api';

const categoryLabels: Record<string, string> = { about: 'About VIT', classrooms: 'Classrooms', labs: 'Labs', events: 'Events', procedures: 'Student services', library: 'Library', it: 'IT support', academics: 'Academics', hostels: 'Hostels', welfare: 'Student welfare', facilities: 'Facilities', accessibility: 'Accessibility', safety: 'Safety', careers: 'Careers', admissions: 'Admissions', admission_info: 'Admissions', research: 'Research', alumni: 'Alumni', global: 'International', international: 'International' };
const suggestions = [
  { label: 'Library borrowing', question: 'What are the library borrowing rules for undergraduate students?' },
  { label: 'Academic rules', question: 'How does the Fully Flexible Credit System work?' },
  { label: 'Hostel admission', question: 'How do freshers book a hostel at VIT Vellore?' },
  { label: 'Student support', question: 'How can I contact student welfare at VIT Vellore?' },
];
const categoryIcons: Record<string, typeof MapPin> = { classrooms: MapPin, labs: Wrench, events: TicketIcon, procedures: FileText, library: LibraryBig, it: Wifi };
function errorText(e: unknown) { return e instanceof Error ? e.message : 'Something went wrong. Please try again.'; }
function RowSkeletons({ count = 5, label }: { count?: number; label: string }) {
  return <div className="skeleton-list" role="status" aria-busy="true"><span className="sr-only">{label}</span>{Array.from({length:count},(_,i)=><div className="skeleton-row" aria-hidden="true" key={i}><Skeleton className="skeleton-icon"/><div className="skeleton-copy"><Skeleton className="skeleton-line short"/><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line medium"/></div></div>)}</div>;
}
function ConversationSkeleton() {
  return <div className="conversation conversation-skeleton" role="status" aria-busy="true"><span className="sr-only">Loading conversation…</span><div aria-hidden="true"><div className="skeleton-user"><Skeleton className="skeleton-bubble"/></div><div className="skeleton-assistant"><Skeleton className="skeleton-avatar"/><div className="skeleton-copy"><Skeleton className="skeleton-line short"/><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line medium"/></div></div><div className="skeleton-user"><Skeleton className="skeleton-bubble narrow"/></div><div className="skeleton-assistant"><Skeleton className="skeleton-avatar"/><div className="skeleton-copy"><Skeleton className="skeleton-line short"/><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line medium"/></div></div></div></div>;
}
// Survives the remount when a first message moves the chat from / to /conversations/:id.
const refocusInput: { current: string | null } = { current: null };
function Spinner() { return <LoaderCircle size={20} className="spinner" aria-hidden="true" />; }

function SourceDialog({ title, children, onClose, provenance }: { title: string; children: ReactNode; onClose: () => void; provenance?: { source_url?: string | null; campus?: string | null; retrieved_at?: string | null } }) {
  const previousFocus = useRef(document.activeElement as HTMLElement | null);
  return <UiDialog open onOpenChange={open => { if (!open) onClose(); }}>
    <DialogContent className="source-dialog" showCloseButton={false} onCloseAutoFocus={event => { event.preventDefault(); previousFocus.current?.focus(); }}>
      <DialogHeader className="source-heading"><div><DialogDescription className="eyebrow">CAMPUS INFORMATION</DialogDescription><DialogTitle>{title}</DialogTitle></div><DialogClose asChild><Button variant="ghost" size="icon" aria-label="Close source"><X size={21} /></Button></DialogClose></DialogHeader>
      <div className="dialog-body">{children}</div>
      <DialogFooter className="source-footer"><ShieldCheck size={19} aria-hidden="true"/><div>{provenance?.source_url ? <><a href={provenance.source_url} target="_blank" rel="noreferrer" className="original-source">Open original VIT source<SquareArrowOutUpRight size={17}/></a><p>{provenance.campus || 'Vellore'}{provenance.retrieved_at && ` · Retrieved ${new Date(provenance.retrieved_at).toLocaleDateString('en-IN', {day:'numeric',month:'short',year:'numeric'})}`}</p></> : <span>Conversation context</span>}</div></DialogFooter>
    </DialogContent>
  </UiDialog>;
}

function CampusSidebar({ onNew }: { onNew: () => void }) {
  const location = useLocation();
  const { setOpenMobile } = useSidebar();
  const account = useAccount();
  const links = [{ to: '/', label: 'Ask a question', icon: MessageSquare }, { to: '/knowledge', label: 'Knowledge base', icon: BookOpen }, { to: '/staff', label: 'Staff queue', icon: Inbox }].filter(link => account?.role === 'staff' ? link.to !== '/' : link.to !== '/staff');
  function closeMenu() { setOpenMobile(false); }
  return <Sidebar className="campus-sidebar" role="navigation" aria-label="Main navigation">
    <SidebarHeader className="campus-sidebar-header">
      <Button className="sidebar-close md:hidden" variant="ghost" size="icon" aria-label="Close navigation" onClick={closeMenu}><X /></Button>
      <NavLink to={account?.role==='staff'?'/staff':'/'} className="brand" onClick={closeMenu}><span className="brand-mark" aria-hidden="true">CH</span><span>Campus Helpdesk<span className="brand-sub">VIT Vellore</span></span></NavLink>
      {account?.role !== 'staff' && <Button asChild variant="secondary" className="new-chat"><NavLink to="/" onClick={() => { onNew(); closeMenu(); }}><Plus size={20} />New conversation</NavLink></Button>}
    </SidebarHeader>
    <SidebarContent><SidebarGroup><SidebarMenu className="campus-nav">
      {links.map(({to,label,icon:Icon}) => <SidebarMenuItem key={to}><SidebarMenuButton asChild isActive={to==='/' ? location.pathname==='/' : location.pathname.startsWith(to)}><NavLink to={to} onClick={closeMenu}><Icon size={21}/><span>{label}</span></NavLink></SidebarMenuButton></SidebarMenuItem>)}
    </SidebarMenu></SidebarGroup>{account?.role !== 'staff' && <ConversationHistory/>}</SidebarContent>
    <SidebarFooter className="campus-sidebar-footer"><span className="avatar" aria-hidden="true">{(account?.username||'?').slice(0,1).toUpperCase()}</span><div className="campus-identity"><strong>{account?.username}</strong><span>{account?.role==='staff'?'Staff account':'Student account'}</span></div></SidebarFooter>
  </Sidebar>;
}

function ConversationHistory() {
  const [rows,setRows]=useState<ConversationSummary[]|null>(null);
  const [error,setError]=useState('');
  const {setOpenMobile}=useSidebar();
  useEffect(()=>{
    let active=true,version=0;
    const load=()=>{const current=++version;void api<ConversationSummary[]>('/conversations').then(data=>{if(active && current===version){setRows(data);setError('');}}).catch(()=>{if(active && current===version)setError('History could not be loaded.');});};
    load();window.addEventListener('campus-conversation-updated',load);
    return()=>{active=false;window.removeEventListener('campus-conversation-updated',load);};
  },[]);
  return <SidebarGroup><SidebarGroupLabel>Conversations</SidebarGroupLabel>
    {error ? <p className="history-error" role="status">{error}<Button variant="link" onClick={conversationChanged}>Retry</Button></p> :
    !rows ? <div className="history-skeleton" role="status" aria-busy="true"><span className="sr-only">Loading conversations…</span>{[0,1,2].map(i=><Skeleton key={i} className="skeleton-history" aria-hidden="true"/>)}</div> :
    <SidebarMenu className="chat-history">{rows.map(row=><SidebarMenuItem key={row.id}><SidebarMenuButton asChild><NavLink to={'/conversations/'+row.id} onClick={()=>setOpenMobile(false)}><MessageSquare size={18}/><span>{row.title}</span></NavLink></SidebarMenuButton></SidebarMenuItem>)}</SidebarMenu>}
  </SidebarGroup>;
}

export default function App() {
  const account = useAccount();
  const liveStatus=useLiveEvents(!!account);
  const [logoutError, setLogoutError] = useState('');
  async function signOut() { try { await api('/auth/session', {method: 'DELETE'}); clearAccess(); } catch (e) {setLogoutError(errorText(e));} }
  const [resetKey, setResetKey] = useState(0);
  const location = useLocation();
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [location.pathname]);
  const name = location.pathname.startsWith('/conversations') ? 'Your conversation' : location.pathname.startsWith('/knowledge') ? 'Knowledge base' : location.pathname.startsWith('/staff') ? 'Staff queue' : 'Ask a question';
  function reset() { try { sessionStorage.removeItem('campus-chat-official-v1'); sessionStorage.removeItem('campus-draft'); sessionStorage.removeItem(`campus-draft:${account?.id || 'student'}:new`); } catch { /* Optional persistence. */ } setResetKey(k=>k+1); }
  return <SidebarProvider className="helpdesk-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <CampusSidebar onNew={reset}/>
    <SidebarInset id="main" className="main-shell"><header className="topbar"><div className="page-location"><SidebarTrigger className="mobile-menu md:hidden" aria-label="Open navigation"/><span>{name}</span></div><span className="live-status" role="status" title={liveStatus} aria-label={liveStatus} data-connected={liveStatus==='Live updates connected'}><span className="connection-dot" aria-hidden="true"/><span className="live-status-text">{liveStatus}</span><span className="mobile-connection-status" aria-hidden="true">{liveStatus==='Connecting to live updates…'?'Connecting…':'Reconnecting…'}</span></span><Button variant="ghost" onClick={() => void signOut()}>Sign out</Button></header>
      {logoutError && <p role="alert">{logoutError}</p>}<Routes><Route path="/" element={account?.role === 'staff' ? <Navigate to="/staff" replace /> : <Chat key={resetKey}/>} /><Route path="/conversations/:conversationId" element={account?.role === 'staff' ? <Navigate to="/staff" replace/> : <Chat/>}/><Route path="/staff/:conversationId" element={account?.role === 'staff' ? <Chat staffMode/> : <Navigate to="/" replace/>}/><Route path="/knowledge" element={<KnowledgeBase/>} /><Route path="/staff" element={account?.role === 'staff' ? <StaffQueue/> : <Navigate to="/" replace />} /><Route path="*" element={<div className="page"><h1>Page not found</h1><Button asChild><NavLink to="/">Back to helpdesk</NavLink></Button></div>} /></Routes>
    </SidebarInset>
  </SidebarProvider>;
}

type ChatMessage = { id: string; role: 'user' | 'assistant' | 'staff'; text: string; sources?: Source[]; outcome?: string; ticket?: string; messageId?: string; offer?: TicketOffer | null; createdAt?: string };
type ConfirmationTarget = { messageId: string; question: string; index: number };
const stateLabels: Record<ConversationState,string> = {ai:'AI helpdesk',waiting_for_staff:'Waiting for staff · AI replies are paused',staff_active:'Chatting with staff · AI replies are paused',resolved:'Resolved · Reopen to contact staff again'};
function Chat({staffMode=false}:{staffMode?:boolean}) {
  const {conversationId}=useParams();
  const navigate=useNavigate();
  const account=useAccount();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversation, setConversation] = useState<string | null>(conversationId || null);
  const [state,setState]=useState<ConversationState>('ai');
  const [ticketReference,setTicketReference]=useState('');
  const [loading,setLoading]=useState(!!conversationId);
  const [loadFailed,setLoadFailed]=useState(false);
  const draftKey=`campus-draft:${account?.id || 'student'}:${conversationId || 'new'}`;
  const [draft, setDraft] = useState(()=>{try{return sessionStorage.getItem(draftKey)||'';}catch{return '';}});
  const draftScope=useRef(draftKey);
  useEffect(()=>{if(draftScope.current===draftKey){try{sessionStorage.setItem(draftKey,draft);}catch{/* Draft remains in memory. */}}},[draft,draftKey]);
  useEffect(()=>{draftScope.current=draftKey;try{setDraft(sessionStorage.getItem(draftKey)||'');}catch{setDraft('');}},[draftKey]);
  const newId=useRef(crypto.randomUUID());
  const retry=useRef<{id:string;content:string;conversation:string}|null>(null);
  const loadVersion=useRef(0);
  function hydrate(data:ConversationDetail) {
    setConversation(data.id);setState(data.state);setTicketReference(data.ticket_reference || '');
    setMessages(data.messages.map(m=>({id:m.id,role:m.role,text:m.content,sources:m.sources,outcome:m.outcome,
      ticket:m.ticket_reference,messageId:m.role==='user'?m.id:m.user_message_id,offer:m.ticket_offer,createdAt:m.created_at})));
  }
  const [pending, setPending] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState('');
  const [error, setError] = useState('');
  const [source, setSource] = useState<Source | null>(null);
  const [escalating, setEscalating] = useState(false);
  const [confirmationTarget, setConfirmationTarget] = useState<ConfirmationTarget | null>(null);
  const transcriptRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const nearBottom = useRef(true);
  const previousMessage = useRef<string | undefined>(undefined);
  const [unseenMessages,setUnseenMessages] = useState(false);
  function updateFades() {
    const transcript=transcriptRef.current;
    if(!transcript)return;
    transcript.dataset.fadeTop=String(transcript.scrollTop>4);
    transcript.dataset.fadeBottom=String(transcript.scrollHeight-transcript.clientHeight-transcript.scrollTop>4);
  }
  function scrollToLatest(smooth=false) {
    const transcript=transcriptRef.current;
    if(transcript){
      const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      if(smooth && !reduced)transcript.scrollTo({top:transcript.scrollHeight,behavior:'smooth'});
      else transcript.scrollTop=transcript.scrollHeight;
    }
    nearBottom.current=true;setUnseenMessages(false);updateFades();
  }
  function trackScroll() {
    const transcript=transcriptRef.current;
    if(!transcript)return;
    nearBottom.current=transcript.scrollHeight-transcript.clientHeight-transcript.scrollTop<64;
    if(nearBottom.current)setUnseenMessages(false);
    updateFades();
  }
  const lock = useRef(false);
  useEffect(()=>{
    const resize=()=>{
      const input=inputRef.current;
      if(!input)return;
      input.style.height='0px';
      input.style.height=`${Math.min(input.scrollHeight,140)}px`;
    };
    resize();window.addEventListener('resize',resize);
    return()=>window.removeEventListener('resize',resize);
  },[draft,conversationId]);
  const confirmationHeading = useRef<HTMLHeadingElement>(null);
  const staffAction = useRef<HTMLButtonElement>(null);
  const hadConfirmation = useRef(false);
  useEffect(() => {
    if (confirmationTarget) confirmationHeading.current?.focus();
    else if (hadConfirmation.current) (staffAction.current ?? inputRef.current)?.focus();
    hadConfirmation.current = !!confirmationTarget;
  }, [confirmationTarget]);
  useEffect(()=>{
    let active=true;
    nearBottom.current=true;previousMessage.current=undefined;setUnseenMessages(false);
    setConversation(conversationId || null);setConfirmationTarget(null);setError('');setMessages([]);setLoadFailed(false);
    if(!conversationId){newId.current=crypto.randomUUID();setMessages([]);setState('ai');setTicketReference('');setLoading(false);return;}
    const load=async()=>{
      const version=++loadVersion.current;
      try{const data=await api<ConversationDetail>(`/conversations/${conversationId}`);if(active && version===loadVersion.current){hydrate(data);setError('');setLoadFailed(false);}}
      catch(e){if(active && version===loadVersion.current){setError(errorText(e));setLoadFailed(true);}}
      finally{if(active && version===loadVersion.current)setLoading(false);}
    };
    setLoading(true);void load();window.addEventListener('campus-conversation-updated',load);
    return()=>{active=false;loadVersion.current++;window.removeEventListener('campus-conversation-updated',load);};
  },[conversationId]);
  useLayoutEffect(() => {
    const latest=messages.at(-1)?.id;
    if(nearBottom.current)scrollToLatest();
    else if(latest && previousMessage.current && latest!==previousMessage.current)setUnseenMessages(true);
    previousMessage.current=latest;
  },[messages,pending]);
  useLayoutEffect(()=>{
    const transcript=transcriptRef.current;
    if(!transcript || typeof ResizeObserver==='undefined')return;
    // Keep the newest message visible as the composer or viewport changes size.
    const observer=new ResizeObserver(()=>{if(nearBottom.current)scrollToLatest();});
    observer.observe(transcript);
    return()=>observer.disconnect();
  },[messages.length>0 || pending || !!conversationId]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || lock.current || loading || loadFailed || state==='resolved' || (staffMode && state!=='staff_active')) return;
    lock.current = true;
    nearBottom.current=true;setUnseenMessages(false);
    setPending(true); setPendingQuestion(question); setError(''); setDraft(''); setConfirmationTarget(null);
    let sentTo: string | null = conversation;
    try {
      let cid=conversation;
      if(!cid){
        const created=await api<ConversationSummary>('/conversations',{method:'POST',body:JSON.stringify({id:newId.current})});
        cid=created.id;setConversation(cid);
      }
      sentTo=cid;
      if(!retry.current || retry.current.content!==question || retry.current.conversation!==cid)
        retry.current={id:crypto.randomUUID(),content:question,conversation:cid};
      const data=await api<ConversationDetail>(`/conversations/${cid}/messages`,{method:'POST',body:JSON.stringify({message:question,client_request_id:retry.current.id})});
      loadVersion.current++;hydrate(data);retry.current=null;setDraft('');
      try{sessionStorage.removeItem(draftKey);}catch{/* Optional browser storage. */}
      if(!conversationId)navigate('/conversations/'+cid,{replace:true});
      conversationChanged();
    } catch (e) { setError(errorText(e)); setDraft(question); }
    finally { setPending(false); setPendingQuestion(''); lock.current = false; refocusInput.current = sentTo; }
  }

  async function raiseTicket(target: ConfirmationTarget) {
    if (!conversation || lock.current) return;
    lock.current = true; setEscalating(true); setError('');
    try {
      const result = await api<{ ticket_reference: string }>(`/conversations/${conversation}/escalate`, {
        method: 'POST', body: JSON.stringify({ message_id: target.messageId, confirmed: true }),
      });
      setTicketReference(result.ticket_reference);
      const data=await api<ConversationDetail>(`/conversations/${conversation}`);hydrate(data);conversationChanged();
      setConfirmationTarget(null);
    } catch (e) { setError(errorText(e)); }
    finally { setEscalating(false); lock.current = false; }
  }

  async function resolveChat() {
    if(!conversation || lock.current)return;
    lock.current=true;setEscalating(true);setError('');
    try{
      const tickets=await api<Ticket[]>('/staff/tickets?status=open');
      const ticket=tickets.find(t=>t.conversation_id===conversation);
      if(!ticket)throw new Error('No open ticket was found. Refresh the conversation.');
      await api(`/staff/tickets/${ticket.id}`,{method:'PATCH',body:JSON.stringify({status:'resolved'})});
      hydrate(await api<ConversationDetail>(`/conversations/${conversation}`));conversationChanged();
    }catch(e){setError(errorText(e));}finally{lock.current=false;setEscalating(false);}
  }
  async function changeState(action:'accept'|'reopen') {
    if(!conversation || lock.current)return;
    lock.current=true;setEscalating(true);setError('');
    try{const data=await api<ConversationDetail>(`/conversations/${conversation}/${action}`,{method:'POST'});hydrate(data);conversationChanged();}
    catch(e){setError(errorText(e));}finally{lock.current=false;setEscalating(false);}
  }
  const disabled=loading || loadFailed || pending || escalating || state==='resolved' || (staffMode && state!=='staff_active');
  const last = messages[messages.length - 1];
  // Consecutive messages from one sender within five minutes share a single name and time header.
  const grouped = messages.map((m,i)=>{const prev=messages[i-1];return !!prev && prev.role===m.role && !(m.createdAt && prev.createdAt && new Date(m.createdAt).getTime()-new Date(prev.createdAt).getTime()>300000);});
  // The textarea is disabled while sending, so focus can only return once it is enabled again.
  useEffect(()=>{ const input=inputRef.current; if(refocusInput.current && refocusInput.current===conversationId && !disabled && input){ input.focus({preventScroll:true}); if(document.activeElement===input)refocusInput.current=null; } });
  const showingConversation = messages.length > 0 || pending || !!conversationId;
  function ticketActions(target: ConfirmationTarget, decline: () => void) {
    return <div className="ticket-actions" role="group" aria-label="Support ticket confirmation">
      <Button variant="default" disabled={disabled} onClick={() => void raiseTicket(target)}>{escalating ? <Spinner /> : <Plus size={19} />}Yes, raise a ticket</Button>
      <Button variant="outline" disabled={disabled} onClick={decline}>No thanks</Button>
    </div>;
  }

  return <div className={`chat-page ${showingConversation ? 'has-messages' : ''}`}>
    {staffMode && <Button asChild variant="link"><NavLink to="/staff">Back to staff queue</NavLink></Button>}
    {(!!conversationId || staffMode || state!=='ai') && <div className="conversation-status" role="status"><span>{stateLabels[state]}</span>{ticketReference && <strong>{ticketReference}</strong>}
      {staffMode && (state==='waiting_for_staff' || state==='staff_active') && <Button variant="outline" disabled={escalating} onClick={()=>void resolveChat()}>Mark resolved</Button>}
      {staffMode && state==='waiting_for_staff' && <Button disabled={escalating} onClick={()=>void changeState('accept')}>Start chat</Button>}
      {!staffMode && state==='resolved' && <Button disabled={escalating} onClick={()=>void changeState('reopen')}>Reopen conversation</Button>}
    </div>}
    {!showingConversation ? <section className="welcome" aria-labelledby="welcome-title">
      <p className="welcome-eyebrow">VIT Vellore</p>
      <h1 id="welcome-title">Ask the helpdesk</h1>
      <p className="welcome-description">Questions about academics, campus services or student support.</p>
    </section> : loading && !messages.length ? <ConversationSkeleton/> : <section ref={transcriptRef} onScroll={trackScroll} className="conversation" aria-label="Conversation">

      {messages.map((m, i) => <article key={m.id} className={`message ${m.role}${grouped[i] ? ' grouped' : ''}`}>
        {m.role !== 'user' && <span className="message-avatar" aria-hidden="true">{m.role === 'staff' ? 'S' : 'AI'}</span>}
        <div className="message-body">
          <div className="message-name">{m.role === 'assistant' ? 'Campus Helpdesk · AI' : m.role === 'staff' ? 'Student support · Staff' : staffMode ? 'Student' : 'You'}{m.createdAt && <time dateTime={m.createdAt}>{new Date(m.createdAt).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})}</time>}</div>
          <p>{m.text}</p>
          {!!m.sources?.length && <div className="answer-sources"><span className="source-label">Sources</span>{m.sources.filter((s,index,all)=>all.findIndex(item=>item.document_id===s.document_id)===index).map(s => <Button key={s.id} variant="outline" className="source-link" onClick={() => setSource({...s,content:m.sources!.filter(item=>item.document_id===s.document_id).map(item=>`${item.heading}\n${item.content}`).join('\n\n')})}><FileText size={18} /><span>{s.title}</span><SquareArrowOutUpRight size={16} /></Button>)}</div>}
          {m.ticket && <div className="ticket-confirmation" role="status"><CheckCircle2 size={21} /><span>Ticket raised · <strong>{m.ticket}</strong></span></div>}
          {!staffMode && state==='ai' && m.offer && i === messages.length - 1 && !m.ticket && ticketActions({ messageId: m.offer.message_id, question: m.offer.query, index: i }, () => void send('No thanks'))}
        </div>
      </article>)}
      {pending && <><article className="message user pending-message"><div className="message-body"><div className="message-name">You</div><p>{pendingQuestion}</p></div></article><div className="working" role="status"><Spinner /><span>{state==='ai' ? 'Searching campus sources…' : 'Saving your message…'}</span></div></>}
      {!staffMode && state==='ai' && !pending && last?.outcome === 'answered' && last.messageId && !last.ticket && !confirmationTarget && <Button ref={staffAction} variant="ghost" className="staff-handoff" onClick={() => setConfirmationTarget({ messageId: last.messageId!, question: messages[messages.length - 2].text, index: messages.length - 1 })}><Headphones size={19} />Ask staff about this answer<ArrowRight size={18} /></Button>}
      {confirmationTarget && <section className="manual-ticket-prompt" aria-label="Confirm support ticket"><h2 ref={confirmationHeading} tabIndex={-1}>Raise a ticket for this question?</h2><p>{confirmationTarget.question}</p>{ticketActions(confirmationTarget, () => setConfirmationTarget(null))}</section>}
    </section>}

    {unseenMessages && <Button variant="outline" className="new-messages" onClick={()=>scrollToLatest(true)}>New messages<ArrowDown size={17} aria-hidden="true"/></Button>}
    <div className="composer-area">
      {error && <Alert variant="destructive" className="error-banner"><HelpCircle size={21} /><AlertDescription>{error}</AlertDescription>{conversationId && <Button variant="outline" onClick={conversationChanged}>Retry</Button>}<Button variant="ghost" size="icon" aria-label="Dismiss error" onClick={() => setError('')}><X size={19} /></Button></Alert>}
      <form className="composer" onSubmit={e => { e.preventDefault(); void send(draft); }}>
        <Label htmlFor="question" className={showingConversation ? "sr-only" : "composer-label"}>{staffMode ? 'Message student' : state==='ai' ? 'Ask a campus question' : 'Message student support'}</Label>
        <Textarea id="question" ref={inputRef} rows={1} maxLength={2000} placeholder={staffMode ? 'Message student…' : state!=='ai' ? 'Message student support…' : showingConversation ? 'Ask a follow-up…' : 'Type your question…'} value={draft} disabled={disabled} onChange={e => setDraft(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(draft); } }} />
        <div className="composer-bottom">{state==='ai' && <span>VIT sources</span>}<Button className="send-button" type="submit" disabled={disabled || !draft.trim()} aria-label={state==='ai' ? 'Send question' : 'Send message'}>{pending ? <Spinner /> : <><span className="send-label">Send</span><ArrowUp size={17} aria-hidden="true"/></>}</Button></div>
      </form>
      <div className="composer-caption"><span className="enter-hint">Enter to send · Shift+Enter for a new line</span></div>
    </div>
    {!staffMode && !showingConversation && <section className="quick-start" aria-labelledby="topics-heading"><div className="quick-start-heading"><h2 id="topics-heading">Suggested questions</h2><NavLink to="/knowledge">Browse sources</NavLink></div>
      <div className="suggestions">{suggestions.map(({label,question})=><Button key={label} variant="ghost" className="suggestion" onClick={()=>{setDraft(question);inputRef.current?.focus({preventScroll:true});}}><span className="suggestion-copy"><strong>{label}</strong><span>{question}</span></span><ArrowRight size={18} className="suggestion-arrow" aria-hidden="true"/></Button>)}</div>
    </section>}
    {source && <SourceDialog provenance={source} title={source.title} onClose={() => setSource(null)}><Badge variant="secondary" className="source-badge">Supporting passage</Badge>{source.heading !== source.title && <h3>{source.heading}</h3>}<p className="source-text">{source.content}</p></SourceDialog>}
  </div>;
}

function KnowledgeBase() {
  const [docs, setDocs] = useState<Knowledge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [selected, setSelected] = useState<Knowledge | null>(null);
  const [visibleCount, setVisibleCount] = useState(15);
  useEffect(()=>setVisibleCount(15),[query,category]);
  useEffect(() => { let active = true; (async () => {
    try { const data = await api<Knowledge[]>('/knowledge'); if (active) setDocs(data); }
    catch { if (active) setError('The knowledge base could not be loaded. Please refresh to try again.'); }
    finally { if (active) setLoading(false); }
  })(); return () => { active = false; }; }, []);
  const filtered = docs.filter(d => (category === 'all' || d.category === category) && query.toLowerCase().trim().split(/\s+/).every(term=>`${d.title} ${d.content}`.toLowerCase().includes(term)));
  return <div className="page knowledge-page"><div className="page-heading"><h1>Knowledge base</h1><p>Public VIT Vellore sources and policy documents.</p></div>
    <div className="knowledge-toolbar"><div className="search-field"><Label htmlFor="knowledge-search" className="sr-only">Search the knowledge base</Label><Search size={21} aria-hidden="true"/><Input id="knowledge-search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search campus information…" />{query && <Button variant="ghost" size="icon" onClick={() => setQuery('')} aria-label="Clear search"><X size={18} /></Button>}</div>{!loading && <span className="result-count">{docs.length} {docs.length===1?'source':'sources'}</span>}</div>
    <div className="category-filter"><Label htmlFor="knowledge-category">Topic</Label><select id="knowledge-category" value={category} onChange={event=>setCategory(event.target.value)}>{['all',...Array.from(new Set(docs.map(d=>d.category))).sort()].map(c=><option key={c} value={c}>{c==='all'?'All topics':categoryLabels[c] || c}</option>)}</select></div>


    {error && <p className="error-banner" role="alert">{error}</p>}
    {loading ? <RowSkeletons count={6} label="Loading campus information…"/> : <><div className="section-heading"><h2>{category === 'all' ? 'All campus information' : categoryLabels[category]}</h2><span>{filtered.length} {filtered.length===1?'result':'results'}</span></div><div className="knowledge-list">{filtered.slice(0,visibleCount).map(d => { const Icon = categoryIcons[d.category] || FileText; return <Button variant="ghost" className="knowledge-row" key={d.id} onClick={() => setSelected(d)}><span className="document-icon"><Icon size={23} strokeWidth={1.7} /></span><span className="document-copy"><span className="document-meta"><span className="chip">{categoryLabels[d.category] || d.category}</span>{d.kind === 'official' ? 'VIT source' : d.kind === 'faq' ? 'FAQ' : 'Guide'}</span><strong>{d.title}</strong><span className="document-excerpt">{d.content.replace(/[#\n]/g, ' ').slice(0, 135)}</span></span><ChevronRight size={21} /></Button>; })}</div>{filtered.length>visibleCount && <Button variant="outline" className="load-sources" onClick={()=>setVisibleCount(n=>n+15)}>Show more sources ({filtered.length-visibleCount} remaining)</Button>}{!filtered.length && <div className="empty-state"><Search size={30} /><h2>No matching sources</h2><p>Try a different search or choose another topic.</p><Button variant="outline" onClick={() => { setQuery(''); setCategory('all'); }}>Clear filters</Button></div>}</>}
    {selected && <SourceDialog provenance={selected} title={selected.title} onClose={() => setSelected(null)}><Badge variant="secondary" className="source-badge">{categoryLabels[selected.category]} · {selected.kind === 'official' ? 'VIT source' : selected.kind === 'faq' ? 'FAQ' : 'Guide'}</Badge><Suspense fallback={<div role="status" aria-busy="true"><span className="sr-only">Loading source…</span><div className="skeleton-copy" aria-hidden="true"><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line"/><Skeleton className="skeleton-line medium"/><Skeleton className="skeleton-line"/></div></div>}><SourceContent content={selected.content} title={selected.title}/></Suspense></SourceDialog>}
  </div>;
}

function StaffQueue() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [status, setStatus] = useState('open');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const requestNumber = useRef(0);
  async function load(filter: string) {
    const request = ++requestNumber.current;
    setLoading(true); setError('');
    try { const data = await api<Ticket[]>(`/staff/tickets?status=${filter}`); if (request === requestNumber.current) { setTickets(data); } }
    catch (e) { if (request === requestNumber.current) setError(errorText(e)); }
    finally { if (request === requestNumber.current) setLoading(false); }
  }
  useEffect(() => { let active=true;const refresh=()=>{if(active)void load(status);};refresh();window.addEventListener('campus-conversation-updated',refresh);return()=>{active=false;requestNumber.current++;window.removeEventListener('campus-conversation-updated',refresh);}; }, [status]);
  return <div className="page"><div className="staff-title"><div className="page-heading"><h1>Staff queue</h1><p>Review confirmed requests and reply to students.</p></div></div><div className="queue-toolbar"><Tabs value={status} onValueChange={setStatus}><TabsList variant="line" aria-label="Ticket status">{['open','resolved','all'].map(value=><TabsTrigger key={value} value={value}>{value==='open'?'Unresolved':value==='resolved'?'Resolved':'All questions'}</TabsTrigger>)}</TabsList></Tabs><Button variant="outline" disabled={loading} onClick={() => void load(status)}>Refresh{loading && <Spinner />}</Button></div>{error && <p className="error-banner" role="alert">{error}</p>}
    {loading ? <RowSkeletons count={4} label="Loading staff queue…"/> : tickets.length ? <div className="ticket-list">{tickets.map(t => <Button variant="ghost" className="ticket-row" key={t.id} asChild><NavLink to={'/staff/'+t.conversation_id}><span className="document-icon"><MessageSquare size={23} /></span><div><span className="document-meta">{t.reference}<span>·</span>{new Date(t.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span><strong>{t.query}</strong><span className="document-excerpt">{t.reason}</span></div><Badge variant="outline" className={`status-pill ${t.status}`}>{t.status === 'open' ? 'Unresolved' : 'Resolved'}</Badge><ChevronRight size={21} /></NavLink></Button>)}</div> : <div className="empty-state queue-empty"><h2>{status === 'open' ? 'No unresolved tickets.' : 'No tickets found.'}</h2><p>{status === 'open' ? 'Questions sent to student support will appear here.' : 'Try another filter to view more questions.'}</p></div>}

  </div>;
}
