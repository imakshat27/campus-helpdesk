export type Account = { id: string; username: string; role: 'student' | 'staff' };
export function clearAccess() {
  try { for (const key of ['campus-access-v1', 'campus-chat-official-v1']) sessionStorage.removeItem(key); } catch { /* Authentication does not depend on browser storage. */ }
  window.dispatchEvent(new Event('campus-access-expired'));
}
