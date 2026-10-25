import { createContext, useContext, useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { LoaderCircle } from 'lucide-react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { api, ApiError } from '../api';
import { clearAccess } from '../access';
import type { Account } from '../access';
export const AccountContext = createContext<Account | null>(null);
export const useAccount = () => useContext(AccountContext);

export default function AccessGate({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [username, setUsername] = useState('');
  const [checking, setChecking] = useState(true);
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    function expired() { setAccount(null); setError('Please sign in to continue. Your draft is kept in this tab.'); }
    window.addEventListener('campus-access-expired', expired);
    void api<Account>('/auth/session').then(user => { if (active) setAccount(user); }).catch(e => { if (active) { clearAccess(); setError(e instanceof ApiError && e.status===401 ? '' : e instanceof Error ? e.message : 'Please sign in again.'); } }).finally(() => { if (active) setChecking(false); });
    return () => { active = false; window.removeEventListener('campus-access-expired', expired); };
  }, []);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setError('');
    try {
      const result = await api<Account>('/auth/session', { method: 'POST', body: JSON.stringify({ username, password }) });
      setPassword(''); setAccount(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'Sign in could not be completed.'); }
    finally { setPending(false); }
  }
  if (account) return <AccountContext.Provider value={account}>{children}</AccountContext.Provider>;
  return <main className="staff-login-page access-page">
    <div className="login-heading"><div className="login-brand"><span className="brand-mark" aria-hidden="true">CH</span><div>Campus Helpdesk<span>VIT Vellore</span></div></div><h1>Sign in</h1><p>Use your student or staff account.</p></div>
    <Card className="login-card">
      {checking ? <p role="status">Checking your session…</p> : <form onSubmit={submit}>
        <Label htmlFor="username">Username</Label>
        <Input id="username" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required maxLength={100} />
        <Label htmlFor="access-password">Password</Label>
        <Input id="access-password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required maxLength={1024} aria-describedby={error ? 'access-error' : undefined} />
        {error && <p id="access-error" className="form-error" role="alert">{error}</p>}
        <Button type="submit" disabled={pending}>{pending ? <><LoaderCircle size={20} className="spinner" aria-hidden="true" />Signing in…</> : 'Sign in'}</Button>
        <p className="login-note">Your sign-in lasts up to 8 hours.</p>
      </form>}
    </Card>
  </main>;
}
