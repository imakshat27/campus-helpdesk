import { useEffect, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { ArrowRight, ArrowUp, BookOpen, Check, CheckCircle2, ChevronRight, Clock3, FileText, GraduationCap, Headphones, HelpCircle, Inbox, LibraryBig, LoaderCircle, MapPin, MessageSquare, Plus, Search, ShieldCheck, SquareArrowOutUpRight, Ticket as TicketIcon, UserRound, Wifi, Wrench, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog as UiDialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose, DialogFooter } from '@/components/ui/dialog';
import { SidebarProvider, Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarInset, SidebarTrigger, useSidebar } from '@/components/ui/sidebar';
import { api } from './api';
import type { ChatReply, Knowledge, Source, Ticket, TicketOffer } from './api';

const categoryLabels: Record<string, string> = { classrooms: 'Classrooms', labs: 'Labs', events: 'Events', procedures: 'Student services', library: 'Library', it: 'IT support' };
const suggestions = [
  { icon: MapPin, label: 'Find a classroom', question: 'Where is SJT 301?', hint: 'Where is SJT 301?' },
  { icon: Clock3, label: 'Check lab timings', question: 'When is the robotics lab open?', hint: 'When is the robotics lab open?' },
  { icon: TicketIcon, label: 'Register for an event', question: 'How do I register for the Campus Hackathon?', hint: 'How do I register for the hackathon?' },
  { icon: FileText, label: 'Student services', question: 'How do I replace a lost student ID?', hint: 'How do I replace a lost student ID?' },
];
const categoryIcons: Record<string, typeof MapPin> = { classrooms: MapPin, labs: Wrench, events: TicketIcon, procedures: FileText, library: LibraryBig, it: Wifi };
function errorText(e: unknown) { return e instanceof Error ? e.message : 'Something went wrong. Please try again.'; }
function Spinner() { return <LoaderCircle size={20} className="spinner" aria-hidden="true" />; }

function SourceDialog({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  const previousFocus = useRef(document.activeElement as HTMLElement | null);
  return <UiDialog open onOpenChange={open => { if (!open) onClose(); }}>
    <DialogContent className="source-dialog" showCloseButton={false} onCloseAutoFocus={event => { event.preventDefault(); previousFocus.current?.focus(); }}>
      <DialogHeader className="source-heading"><div><DialogDescription className="eyebrow">CAMPUS INFORMATION</DialogDescription><DialogTitle>{title}</DialogTitle></div><DialogClose asChild><Button variant="ghost" size="icon" aria-label="Close source"><X size={21} /></Button></DialogClose></DialogHeader>
      <div className="dialog-body">{children}</div>
      <DialogFooter className="source-footer"><ShieldCheck size={19} /><span>Sample campus information · 16 Oct 2026</span></DialogFooter>
    </DialogContent>
  </UiDialog>;
}

function CampusSidebar({ onNew }: { onNew: () => void }) {
  const location = useLocation();
  const { setOpenMobile } = useSidebar();
  const links = [{ to: '/', label: 'Ask a question', icon: MessageSquare }, { to: '/knowledge', label: 'Knowledge base', icon: BookOpen }, { to: '/staff', label: 'Staff queue', icon: Inbox }];
  function closeMenu() { setOpenMobile(false); }
  return <Sidebar className="campus-sidebar" role="navigation" aria-label="Main navigation">
    <SidebarHeader className="campus-sidebar-header">
      <Button className="sidebar-close md:hidden" variant="ghost" size="icon" aria-label="Close navigation" onClick={closeMenu}><X /></Button>
      <NavLink to="/" className="brand" onClick={closeMenu}><span className="brand-mark"><GraduationCap size={27} strokeWidth={1.7} /></span><span>Campus<span className="brand-sub">Helpdesk</span></span></NavLink>
      <Button asChild variant="secondary" className="new-chat"><NavLink to="/" onClick={() => { onNew(); closeMenu(); }}><Plus size={20} />New conversation</NavLink></Button>
    </SidebarHeader>
    <SidebarContent><SidebarGroup><SidebarGroupLabel className="campus-nav-label">Helpdesk</SidebarGroupLabel><SidebarMenu className="campus-nav">
      {links.map(({to,label,icon:Icon}) => <SidebarMenuItem key={to}><SidebarMenuButton asChild isActive={to==='/' ? location.pathname==='/' : location.pathname.startsWith(to)}><NavLink to={to} onClick={closeMenu}><Icon size={21}/><span>{label}</span></NavLink></SidebarMenuButton></SidebarMenuItem>)}
    </SidebarMenu></SidebarGroup></SidebarContent>
    <SidebarFooter className="campus-sidebar-footer"><div className="sample-note"><BookOpen size={19} aria-hidden="true"/><p>Sample information<span>Prototype content</span></p></div><Separator /><div className="campus-identity"><span className="university-avatar">V</span><div><strong>VIT campus</strong><span>Student support</span></div></div></SidebarFooter>
  </Sidebar>;
}

export default function App() {
  const [resetKey, setResetKey] = useState(0);
  const location = useLocation();
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [location.pathname]);
  const name = location.pathname.startsWith('/knowledge') ? 'Knowledge base' : location.pathname.startsWith('/staff') ? 'Staff queue' : 'Ask a question';
  function reset() { try { sessionStorage.removeItem('campus-chat'); } catch { /* Optional persistence. */ } setResetKey(k=>k+1); }
  return <SidebarProvider className="helpdesk-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <CampusSidebar onNew={reset}/>
    <SidebarInset id="main" className="main-shell"><header className="topbar"><div className="page-location"><SidebarTrigger className="mobile-menu md:hidden" aria-label="Open navigation"/><span>{name}</span></div><span className="workspace-context"><GraduationCap size={18} aria-hidden="true"/>Student support</span></header>
      <Routes><Route path="/" element={<Chat key={resetKey}/>} /><Route path="/knowledge" element={<KnowledgeBase/>} /><Route path="/staff" element={<StaffQueue/>} /><Route path="*" element={<div className="page"><h1>Page not found</h1><Button asChild><NavLink to="/">Back to helpdesk</NavLink></Button></div>} /></Routes>
    </SidebarInset>
  </SidebarProvider>;
}

function readChat(): { messages: ChatMessage[]; conversation: string | null } {
  try { const saved = JSON.parse(sessionStorage.getItem('campus-chat') || 'null'); if (saved && Array.isArray(saved.messages) && typeof saved.conversation === 'string') return saved; } catch { /* Storage may be unavailable. */ }
  return { messages: [], conversation: null };
}
type ChatMessage = { role: 'user' | 'assistant'; text: string; sources?: Source[]; outcome?: string; ticket?: string; messageId?: string; offer?: TicketOffer | null };
type ConfirmationTarget = { messageId: string; question: string; index: number };
function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => readChat().messages);
  const [conversation, setConversation] = useState<string | null>(() => readChat().conversation);
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState('');
  const [error, setError] = useState('');
  const [source, setSource] = useState<Source | null>(null);
  const [escalating, setEscalating] = useState(false);
  const [confirmationTarget, setConfirmationTarget] = useState<ConfirmationTarget | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const lock = useRef(false);
  const confirmationHeading = useRef<HTMLHeadingElement>(null);
  const staffAction = useRef<HTMLButtonElement>(null);
  const hadConfirmation = useRef(false);
  useEffect(() => {
    if (confirmationTarget) confirmationHeading.current?.focus();
    else if (hadConfirmation.current) (staffAction.current ?? inputRef.current)?.focus();
    hadConfirmation.current = !!confirmationTarget;
  }, [confirmationTarget]);
  useEffect(() => { if (conversation) { try { sessionStorage.setItem('campus-chat', JSON.stringify({ messages, conversation })); } catch { /* Chat still works without storage. */ } } }, [messages, conversation]);
  useEffect(() => { if (messages.length || pending) endRef.current?.scrollIntoView?.({ behavior: 'instant', block: 'end' }); }, [messages, pending]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || lock.current) return;
    lock.current = true;
    setPending(true); setPendingQuestion(question); setError(''); setDraft(''); setConfirmationTarget(null);
    try {
      const reply = await api<ChatReply>('/chat', { method: 'POST', body: JSON.stringify({ message: question, conversation_id: conversation }) });
      setConversation(reply.conversation_id);
      setMessages(m => [...m,
        { role: 'user', text: question, messageId: reply.user_message_id },
        { role: 'assistant', text: reply.message, sources: reply.sources, outcome: reply.outcome, ticket: reply.ticket_reference, messageId: reply.user_message_id, offer: reply.ticket_offer },
      ]);
    } catch (e) { setError(errorText(e)); setDraft(question); }
    finally { setPending(false); setPendingQuestion(''); lock.current = false; inputRef.current?.focus(); }
  }

  async function raiseTicket(target: ConfirmationTarget) {
    if (!conversation || lock.current) return;
    lock.current = true; setEscalating(true); setError('');
    try {
      const result = await api<{ ticket_reference: string }>(`/conversations/${conversation}/escalate`, {
        method: 'POST', body: JSON.stringify({ message_id: target.messageId, confirmed: true }),
      });
      setMessages(current => current.map((message, index) => index === target.index ? { ...message, ticket: result.ticket_reference, outcome: 'escalated', offer: null } : message));
      setConfirmationTarget(null);
    } catch (e) { setError(errorText(e)); }
    finally { setEscalating(false); lock.current = false; }
  }

  const last = messages[messages.length - 1];
  const showingConversation = messages.length > 0 || pending;
  function ticketActions(target: ConfirmationTarget, decline: () => void) {
    return <div className="ticket-actions" role="group" aria-label="Support ticket confirmation">
      <Button variant="default" disabled={pending || escalating} onClick={() => void raiseTicket(target)}>{escalating ? <Spinner /> : <Plus size={19} />}Yes, raise a ticket</Button>
      <Button variant="outline" disabled={pending || escalating} onClick={decline}>No thanks</Button>
    </div>;
  }

  return <div className={`chat-page ${showingConversation ? 'has-messages' : ''}`}>
    {!showingConversation ? <section className="welcome" aria-labelledby="welcome-title">
      <span className="welcome-context">VIT · Student helpdesk</span>
      <h1 id="welcome-title">A question about campus?</h1>
      <p className="welcome-description">Find a room, check lab hours, or get help with a campus procedure.</p>
    </section> : <section className="conversation" aria-label="Conversation">
      <div className="conversation-start"><strong>Your conversation</strong><span>Campus Helpdesk</span></div>
      {messages.map((m, i) => <article key={i} className={`message ${m.role}`}>
        <div className="message-avatar" aria-hidden="true">{m.role === 'assistant' ? <GraduationCap size={22} /> : <UserRound size={21} />}</div>
        <div className="message-body">
          <div className="message-name">{m.role === 'assistant' ? 'Campus Helpdesk' : 'You'}</div>
          <p>{m.text}</p>
          {!!m.sources?.length && <div className="answer-sources"><span className="source-label">Sources</span>{m.sources.map(s => <Button key={s.id} variant="outline" className="source-link" onClick={() => setSource(s)}><FileText size={18} /><span>{s.title}</span><SquareArrowOutUpRight size={16} /></Button>)}</div>}
          {m.ticket && <div className="ticket-confirmation" role="status"><CheckCircle2 size={21} /><span>Ticket raised · <strong>{m.ticket}</strong></span></div>}
          {m.offer && i === messages.length - 1 && !m.ticket && ticketActions({ messageId: m.offer.message_id, question: m.offer.query, index: i }, () => void send('No thanks'))}
        </div>
      </article>)}
      {pending && <><article className="message user"><div className="message-avatar" aria-hidden="true"><UserRound size={21} /></div><div className="message-body"><div className="message-name">You</div><p>{pendingQuestion}</p></div></article><div className="working" role="status"><Spinner /><span>Working on your question…</span></div></>}
      {!pending && last?.outcome === 'answered' && last.messageId && !last.ticket && !confirmationTarget && <Button ref={staffAction} variant="ghost" className="staff-handoff" onClick={() => setConfirmationTarget({ messageId: last.messageId!, question: messages[messages.length - 2].text, index: messages.length - 1 })}><Headphones size={19} />Ask staff about this answer<ArrowRight size={18} /></Button>}
      {confirmationTarget && <section className="manual-ticket-prompt" aria-label="Confirm support ticket"><h2 ref={confirmationHeading} tabIndex={-1}>Raise a ticket for this question?</h2><p>{confirmationTarget.question}</p>{ticketActions(confirmationTarget, () => setConfirmationTarget(null))}</section>}
      <div ref={endRef} />
    </section>}

    <div className="composer-area">
      {error && <Alert variant="destructive" className="error-banner"><HelpCircle size={21} /><AlertDescription>{error}</AlertDescription><Button variant="ghost" size="icon" aria-label="Dismiss error" onClick={() => setError('')}><X size={19} /></Button></Alert>}
      <form className="composer" onSubmit={e => { e.preventDefault(); void send(draft); }}>
        <Label htmlFor="question" className={showingConversation ? "sr-only" : "composer-label"}>Ask a campus question</Label>
        <Textarea id="question" ref={inputRef} rows={2} maxLength={2000} placeholder={showingConversation ? 'Ask a follow-up…' : 'For example, where is SJT 301?'} value={draft} disabled={pending || escalating} onChange={e => setDraft(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(draft); } }} />
        <div className="composer-bottom"><span><BookOpen size={18} aria-hidden="true"/>Answers include sources</span><Button className="send-button" type="submit" disabled={pending || escalating || !draft.trim()} aria-label="Send question">{pending ? <Spinner /> : <><span>Send question</span><ArrowUp size={19} aria-hidden="true"/></>}</Button></div>
      </form>
      <div className="composer-caption"><span>Sample information · 16 Oct 2026</span><span className="enter-hint">Enter to send <span className="keycap">↵</span></span></div>
    </div>
    {!showingConversation && <section className="quick-start" aria-labelledby="topics-heading"><div className="quick-start-heading"><span id="topics-heading">Try a question</span><Button asChild variant="link"><NavLink to="/knowledge">Browse FAQs<ArrowRight size={17}/></NavLink></Button></div>
      <div className="suggestions">{suggestions.map(({icon:Icon,label,question,hint})=><Card key={label} className="topic-card"><Button variant="ghost" className="suggestion" onClick={()=>{setDraft(question);inputRef.current?.focus();}}><Icon size={21}/><span className="suggestion-copy"><strong>{label}</strong><span>{hint}</span></span><ChevronRight size={18}/></Button></Card>)}</div>
    </section>}
    {source && <SourceDialog title={source.title} onClose={() => setSource(null)}><Badge variant="secondary" className="source-badge">Supporting passage</Badge>{source.heading !== source.title && <h3>{source.heading}</h3>}<p className="source-text">{source.content}</p></SourceDialog>}
  </div>;
}

function KnowledgeBase() {
  const [docs, setDocs] = useState<Knowledge[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [selected, setSelected] = useState<Knowledge | null>(null);
  useEffect(() => { let active = true; (async () => {
    try { const data = await api<Knowledge[]>('/knowledge'); if (active) setDocs(data); }
    catch { try { const response = await fetch('/sample-knowledge.json'); if (!response.ok) throw new Error(); const data = await response.json(); if (active) { setDocs(data); setPreview(true); } } catch { if (active) setError('The knowledge base could not be loaded. Please refresh to try again.'); } }
    finally { if (active) setLoading(false); }
  })(); return () => { active = false; }; }, []);
  const filtered = docs.filter(d => (category === 'all' || d.category === category) && `${d.title} ${d.content}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="page knowledge-page"><div className="page-heading"><span className="eyebrow">CAMPUS INFORMATION</span><h1>Knowledge base</h1><p>Search FAQs and guides for classroom details, campus procedures, and events.</p></div>
    <div className="knowledge-toolbar"><div className="search-field"><Label htmlFor="knowledge-search" className="sr-only">Search the knowledge base</Label><Search size={21} aria-hidden="true"/><Input id="knowledge-search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search campus information…" />{query && <Button variant="ghost" size="icon" onClick={() => setQuery('')} aria-label="Clear search"><X size={18} /></Button>}</div>{!loading && <span className="result-count">{docs.length} sources</span>}</div>
    <ToggleGroup type="single" variant="outline" spacing={2} value={category} onValueChange={value=>{if(value)setCategory(value);}} className="filters" aria-label="Filter by category">{['all', ...Object.keys(categoryLabels)].map(c => <ToggleGroupItem key={c} value={c}>{c === 'all' ? 'All topics' : categoryLabels[c]}</ToggleGroupItem>)}</ToggleGroup>

    {preview && <div className="notice"><BookOpen size={20} /><span>Viewing bundled sample sources. Live database connection is unavailable.</span></div>}
    {error && <p className="error-banner" role="alert">{error}</p>}
    {loading ? <div className="empty-state"><Spinner /><p>Loading campus information…</p></div> : <><div className="section-heading"><h2>{category === 'all' ? 'All campus information' : categoryLabels[category]}</h2><span>{filtered.length} results</span></div><div className="knowledge-list">{filtered.map(d => { const Icon = categoryIcons[d.category] || FileText; return <Button variant="ghost" className="knowledge-row" key={d.id} onClick={() => setSelected(d)}><span className="document-icon"><Icon size={23} strokeWidth={1.7} /></span><span className="document-copy"><span className="document-meta">{categoryLabels[d.category]}<span>·</span>{d.kind === 'faq' ? 'FAQ' : 'Guide'}</span><strong>{d.title}</strong><span className="document-excerpt">{d.content.replace(/[#\n]/g, ' ').slice(0, 135)}</span></span><ChevronRight size={21} /></Button>; })}</div>{!filtered.length && <div className="empty-state"><Search size={30} /><h2>No matching sources</h2><p>Try a different search or choose another topic.</p><Button variant="outline" onClick={() => { setQuery(''); setCategory('all'); }}>Clear filters</Button></div>}</>}
    {selected && <SourceDialog title={selected.title} onClose={() => setSelected(null)}><Badge variant="secondary" className="source-badge">{categoryLabels[selected.category]} · {selected.kind === 'faq' ? 'FAQ' : 'Guide'}</Badge><SourceContent content={selected.content} title={selected.title} /></SourceDialog>}
  </div>;
}
function SourceContent({ content, title }: { content: string; title: string }) { return <div className="source-document">{content.split('\n').filter((line,i)=>!(i===0 && line.replace(/^#+\s*/, '').trim()===title)).map((line, i) => line.startsWith('# ') ? <h3 key={i}>{line.slice(2)}</h3> : line.startsWith('## ') ? <h3 key={i}>{line.slice(3)}</h3> : line.trim() ? <p key={i}>{line}</p> : null)}</div>; }

function StaffQueue() {
  const [credentials, setCredentials] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [status, setStatus] = useState('open');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [updating, setUpdating] = useState(false);
  const requestNumber = useRef(0);
  async function load(auth: string, filter: string) {
    const request = ++requestNumber.current;
    setLoading(true); setError('');
    try { const data = await api<Ticket[]>(`/staff/tickets?status=${filter}`, { headers: { Authorization: `Basic ${auth}` } }); if (request === requestNumber.current) { setTickets(data); setCredentials(auth); } }
    catch (e) { if (request === requestNumber.current) setError(errorText(e)); }
    finally { if (request === requestNumber.current) setLoading(false); }
  }
  function login(e: FormEvent) { e.preventDefault(); const bytes = new TextEncoder().encode(`${username}:${password}`); void load(btoa(Array.from(bytes, b => String.fromCharCode(b)).join('')), status); }
  async function resolve(ticket: Ticket) {
    setUpdating(true); setError('');
    try { await api(`/staff/tickets/${ticket.id}`, { method: 'PATCH', headers: { Authorization: `Basic ${credentials}` }, body: JSON.stringify({ status: ticket.status === 'open' ? 'resolved' : 'open' }) }); setSelected(null); await load(credentials, status); }
    catch (e) { setError(errorText(e)); }
    finally { setUpdating(false); }
  }
  if (!credentials) return <div className="staff-login-page"><div className="login-heading"><span className="welcome-symbol"><ShieldCheck size={31} strokeWidth={1.5} /></span><span className="eyebrow">STUDENT SUPPORT</span><h1>Staff access</h1><p>Sign in to review questions that need a human answer.</p></div><Card className="login-card"><form onSubmit={login}><h2>Staff sign in</h2><Label htmlFor="username">Username</Label><Input id="username" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required /><Label htmlFor="password">Password</Label><Input id="password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required />{error && <p className="form-error" role="alert">{error}</p>}<Button type="submit" disabled={loading}>{loading ? <Spinner /> : <>Sign in<ArrowRight size={19} /></>}</Button><p className="login-note"><ShieldCheck size={18} />For student support staff only.</p></form></Card></div>;
  return <div className="page"><div className="staff-title"><div className="page-heading"><span className="eyebrow">STUDENT SUPPORT</span><h1>Staff queue</h1><p>Review questions sent to student support and track their resolution.</p></div><Button variant="outline" onClick={() => { requestNumber.current++; setLoading(false); setCredentials(''); setPassword(''); setTickets([]); setSelected(null); }}>Sign out</Button></div><div className="queue-toolbar"><Tabs value={status} onValueChange={value=>{setStatus(value);void load(credentials,value);}}><TabsList aria-label="Ticket status">{['open','resolved','all'].map(value=><TabsTrigger key={value} value={value}>{value==='open'?'Unresolved':value==='resolved'?'Resolved':'All questions'}</TabsTrigger>)}</TabsList></Tabs><Button variant="outline" disabled={loading} onClick={() => void load(credentials, status)}>Refresh{loading && <Spinner />}</Button></div>{error && <p className="error-banner" role="alert">{error}</p>}
    {loading ? <div className="empty-state"><Spinner /><p>Loading staff queue…</p></div> : tickets.length ? <div className="ticket-list">{tickets.map(t => <Button variant="ghost" className="ticket-row" key={t.id} onClick={() => setSelected(t)}><span className="document-icon"><MessageSquare size={23} /></span><div><span className="document-meta">{t.reference}<span>·</span>{new Date(t.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span><strong>{t.query}</strong><span className="document-excerpt">{t.reason}</span></div><Badge variant="outline" className={`status-pill ${t.status}`}>{t.status === 'open' ? 'Unresolved' : 'Resolved'}</Badge><ChevronRight size={21} /></Button>)}</div> : <div className="empty-state queue-empty"><CheckCircle2 size={38} strokeWidth={1.4} /><h2>{status === 'open' ? 'No unresolved tickets.' : 'No tickets found.'}</h2><p>{status === 'open' ? 'Questions sent to student support will appear here.' : 'Try another filter to view more questions.'}</p></div>}
    {selected && <SourceDialog title={selected.reference} onClose={() => { if (!updating) setSelected(null); }}><Badge variant="outline" className={`status-pill ${selected.status}`}>{selected.status === 'open' ? 'Unresolved' : 'Resolved'}</Badge><h3>{selected.query}</h3><div className="ticket-context">{selected.messages.map((m, i) => <div key={i}><strong>{m.role === 'user' ? 'Student' : 'Helpdesk'}</strong><p>{m.content}</p></div>)}</div>{error && <p role="alert" className="form-error">{error}</p>}<Button variant="default" disabled={updating} onClick={() => void resolve(selected)}>{updating ? <Spinner /> : <Check size={19} />}{selected.status === 'open' ? 'Mark resolved' : 'Reopen question'}</Button></SourceDialog>}
  </div>;
}
