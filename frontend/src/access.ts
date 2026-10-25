export type Account = { id: string; username: string; role: 'student' | 'staff' };
export function clearAccess() {
  for (const key of ['campus-access-v1', 'campus-chat-official-v1']) sessionStorage.removeItem(key);
  window.dispatchEvent(new Event('campus-access-expired'));
}
