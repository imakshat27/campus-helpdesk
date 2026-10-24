const key = 'campus-access-v1';
let current = '';
export function accessToken(): string {
  try { return current || sessionStorage.getItem(key) || ''; } catch { return current; }
}
export function saveAccess(token: string) {
  current = token;
  try { sessionStorage.setItem(key, token); sessionStorage.removeItem('campus-chat-official-v1'); } catch { /* Tab storage is optional. */ }
}
export function clearAccess() {
  current = '';
  try { sessionStorage.removeItem(key); sessionStorage.removeItem('campus-chat-official-v1'); } catch { /* Tab storage is optional. */ }
  window.dispatchEvent(new Event('campus-access-expired'));
}
