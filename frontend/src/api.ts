export type Knowledge = { id: string; title: string; category: string; kind: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type Source = { id: string; document_id: string; title: string; heading: string; content: string; source_url?: string | null; campus?: string | null; retrieved_at?: string | null };
export type TicketOffer = { message_id: string; query: string };
export type ChatReply = { conversation_id: string; outcome: 'answered' | 'clarification' | 'needs_staff_confirmation' | 'conversation' | 'escalated'; message: string; sources: Source[]; ticket_reference?: string; user_message_id: string; ticket_offer?: TicketOffer | null };
export type Ticket = { id: string; reference: string; query: string; reason: string; status: 'open' | 'resolved'; created_at: string; messages: { role: string; content: string }[] };
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try { response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers }, signal: options.signal ?? AbortSignal.timeout(100000) }); }
  catch { throw new Error('Could not reach the helpdesk. Check your connection and try again.'); }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'This request could not be completed. Please try again.');
  }
  return response.json();
}
