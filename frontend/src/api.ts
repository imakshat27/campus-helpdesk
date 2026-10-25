export type Knowledge = { id: string; title: string; category: string; kind: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type Source = { id: string; document_id: string; title: string; heading: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type TicketOffer = { message_id: string; query: string };
export type ChatReply = { conversation_id: string; outcome: 'answered' | 'clarification' | 'needs_staff_confirmation' | 'conversation' | 'escalated'; message: string; sources: Source[]; ticket_reference?: string; user_message_id: string; ticket_offer?: TicketOffer | null };
export type Ticket = { id: string; conversation_id: string; reference: string; query: string; reason: string; status: 'open' | 'resolved'; created_at: string; messages: { role: string; content: string }[] };
import { clearAccess } from './access';
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  // Vite embeds this public URL at build time. Credentials remain on Render.
  const base = '/api';
  let response: Response;
  try { response = await fetch(`${base}${path}`, { ...options, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...options.headers }, signal: options.signal ?? AbortSignal.timeout(100000) }); }
  catch { throw new Error('Could not reach the helpdesk. Check your connection and try again.'); }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/')) clearAccess();
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'This request could not be completed. Please try again.');
  }
  return response.json();
}

export type ConversationState = 'ai' | 'waiting_for_staff' | 'staff_active' | 'resolved';
export type ConversationSummary = { id: string; title: string; state: ConversationState; created_at: string; updated_at: string };
export type StoredMessage = { id: string; role: 'user' | 'assistant' | 'staff'; content: string; sources: Source[]; outcome?: string; user_message_id?: string; ticket_reference?: string; ticket_offer?: TicketOffer | null; created_at: string; sequence: number };
export type ConversationDetail = ConversationSummary & { conversation_id: string; ticket_reference?: string; messages: StoredMessage[] };
export function conversationChanged() { window.dispatchEvent(new Event('campus-conversation-updated')); }
