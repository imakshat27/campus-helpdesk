import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AccessGate from './AccessGate';
import { accessToken, clearAccess, saveAccess } from '../access';

const request=vi.fn();
beforeEach(() => { clearAccess(); sessionStorage.clear(); vi.stubGlobal('fetch',request); });
afterEach(() => { cleanup(); clearAccess(); request.mockReset(); vi.unstubAllGlobals(); });
function show() { render(<AccessGate><p>Protected chat</p></AccessGate>); }

it('requires a password before mounting protected screens', () => {
  show();
  expect(screen.getByLabelText('Access password')).toHaveAttribute('type','password');
  expect(screen.queryByText('Protected chat')).not.toBeInTheDocument();
  expect(request).not.toHaveBeenCalled();
});

it('keeps incorrect login errors beside the form without granting access', async () => {
  request.mockResolvedValue({ ok:false,status:401,json:async()=>({detail:'Incorrect access password.'}) });
  show(); const user=userEvent.setup();
  await user.type(screen.getByLabelText('Access password'),'wrong');
  await user.click(screen.getByRole('button',{name:'Continue'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect access password.');
  expect(screen.queryByText('Protected chat')).not.toBeInTheDocument();
  expect(accessToken()).toBe('');
});

it('uses the server-issued session and signs out while preserving the draft', async () => {
  request.mockResolvedValue({ ok:true,status:200,json:async()=>({access_token:'server-signed-session'}) });
  show();const user=userEvent.setup();
  await user.type(screen.getByLabelText('Access password'),'review-access-password');
  await user.click(screen.getByRole('button',{name:'Continue'}));
  expect(await screen.findByText('Protected chat')).toBeVisible();
  expect(accessToken()).toBe('server-signed-session');
  sessionStorage.setItem('campus-draft','My unsent question');
  const { act }=await import('@testing-library/react');
  act(()=>clearAccess());
  expect(await screen.findByLabelText('Access password')).toBeVisible();
  expect(sessionStorage.getItem('campus-draft')).toBe('My unsent question');
  expect(accessToken()).toBe('');
});

it('does not trust an expired token saved in tab storage', async () => {
  saveAccess('expired-session');
  request.mockResolvedValue({ ok:false,status:401,json:async()=>({detail:'Your session has expired. Please sign in again.'}) });
  show();
  expect(await screen.findByRole('alert')).toHaveTextContent('Your session has expired.');
  expect(screen.queryByText('Protected chat')).not.toBeInTheDocument();
  expect(accessToken()).toBe('');
});
