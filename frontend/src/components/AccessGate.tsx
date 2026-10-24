import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { ArrowRight, LoaderCircle, ShieldCheck } from 'lucide-react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { api } from '../api';
import { accessToken, clearAccess, saveAccess } from '../access';

export default function AccessGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [checking, setChecking] = useState(!!accessToken());
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    function expired() { setReady(false); setError('Please sign in to continue. Your draft is kept in this tab.'); }
    window.addEventListener('campus-access-expired', expired);
    if (accessToken()) void api('/auth/session').then(() => { if (active) setReady(true); }).catch(e => { if (active) { clearAccess(); setError(e instanceof Error ? e.message : 'Please sign in again.'); } }).finally(() => { if (active) setChecking(false); });
    return () => { active = false; window.removeEventListener('campus-access-expired', expired); };
  }, []);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setError('');
    try {
      const result = await api<{ access_token: string }>('/auth/session', { method: 'POST', body: JSON.stringify({ password }) });
      saveAccess(result.access_token); setPassword(''); setReady(true);
    } catch (e) { setError(e instanceof Error ? e.message : 'Sign in could not be completed.'); }
    finally { setPending(false); }
  }
  if (ready) return children;
  return <main className="staff-login-page access-page">
    <div className="login-heading"><span className="welcome-symbol"><ShieldCheck size={31} strokeWidth={1.5} aria-hidden="true" /></span><span className="eyebrow">VIT · STUDENT HELPDESK</span><h1>Private review access</h1><p>Enter the access password shared by the project owner.</p></div>
    <Card className="login-card">
      {checking ? <p role="status">Checking your session…</p> : <form onSubmit={submit}>
        <Label htmlFor="access-password">Access password</Label>
        <Input id="access-password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required maxLength={1024} aria-describedby={error ? 'access-error' : undefined} />
        {error && <p id="access-error" className="form-error" role="alert">{error}</p>}
        <Button type="submit" disabled={pending}>{pending ? <><LoaderCircle size={20} className="spinner" aria-hidden="true" />Signing in…</> : <>Continue<ArrowRight size={19} aria-hidden="true" /></>}</Button>
        <p className="login-note">Access lasts up to 8 hours in this tab.</p>
      </form>}
    </Card>
  </main>;
}
