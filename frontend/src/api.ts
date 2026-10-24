export type Knowledge = { id: string; title: string; category: string; kind: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type Source = { id: string; document_id: string; title: string; heading: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type TicketOffer = { message_id: string; query: string };
export type ChatReply = { conversation_id: string; outcome: 'answered' | 'clarification' | 'needs_staff_confirmation' | 'conversation' | 'escalated'; message: string; sources: Source[]; ticket_reference?: string; user_message_id: string; ticket_offer?: TicketOffer | null };
export type Ticket = { id: string; reference: string; query: string; reason: string; status: 'open' | 'resolved'; created_at: string; messages: { role: string; content: string }[] };
import { accessToken, clearAccess } from './access';
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  // Vite embeds this public URL at build time. Credentials remain on Render.
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');
  let response: Response;
  const token = accessToken();
  try { response = await fetch(`${base}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }, signal: options.signal ?? AbortSignal.timeout(100000) }); }
  catch { throw new Error('Could not reach the helpdesk. Check your connection and try again.'); }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/') && !path.startsWith('/staff/')) clearAccess();
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'This request could not be completed. Please try again.');
  }
  return response.json();
}
