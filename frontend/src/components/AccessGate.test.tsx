import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AccessGate from './AccessGate';
const request=vi.fn();
beforeEach(()=>{sessionStorage.clear();vi.stubGlobal('fetch',request);request.mockResolvedValue({ok:false,status:401,json:async()=>({detail:'Please sign in again.'})});});
afterEach(()=>{cleanup();request.mockReset();vi.unstubAllGlobals();});
function show(){render(<AccessGate><p>Protected chat</p></AccessGate>);}
it('checks the server session before displaying the shared account form',async()=>{
 show();expect(await screen.findByLabelText('Username')).toBeVisible();expect(screen.queryByRole('alert')).not.toBeInTheDocument();expect(screen.getByLabelText('Password')).toHaveAttribute('type','password');expect(screen.queryByText('Protected chat')).not.toBeInTheDocument();
});
it('keeps incorrect login errors beside the form',async()=>{
 show();const user=userEvent.setup();await user.type(await screen.findByLabelText('Username'),'student');await user.type(screen.getByLabelText('Password'),'wrong');
 request.mockResolvedValue({ok:false,status:401,json:async()=>({detail:'Incorrect username or password.'})});
 await user.click(screen.getByRole('button',{name:'Sign in'}));expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect username');expect(screen.queryByText('Protected chat')).not.toBeInTheDocument();
});
it('uses the cookie-backed account without storing a token',async()=>{
 show();const user=userEvent.setup();await user.type(await screen.findByLabelText('Username'),'student');await user.type(screen.getByLabelText('Password'),'private-password');
 request.mockResolvedValue({ok:true,json:async()=>({id:'1',username:'student',role:'student'})});await user.click(screen.getByRole('button',{name:'Sign in'}));expect(await screen.findByText('Protected chat')).toBeVisible();expect(sessionStorage.getItem('campus-access-v1')).toBeNull();
});
