import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useLiveEvents } from './use-live-events';
const mocks=vi.hoisted(()=>({api:vi.fn(),changed:vi.fn(),clear:vi.fn()}));
vi.mock('../api',()=>({api:mocks.api,conversationChanged:mocks.changed}));
vi.mock('../access',()=>({clearAccess:mocks.clear}));
class Socket {
 static CLOSED=3;
 static all:Socket[]=[];
 readyState=0;
 onopen:(()=>void)|null=null;
 onmessage:((event:{data:string})=>void)|null=null;
 onclose:((event:{code:number})=>void)|null=null;
 onerror:(()=>void)|null=null;
 send=vi.fn();
 constructor(public url:string){Socket.all.push(this);}
 close(){this.readyState=3;this.onclose?.({code:1006});}
 open(){this.readyState=1;this.onopen?.();}
 event(type:string){this.onmessage?.({data:JSON.stringify({type})});}
}
beforeEach(()=>{vi.useFakeTimers();Socket.all=[];vi.stubGlobal('WebSocket',Socket);mocks.api.mockResolvedValue({ticket:'one-use-ticket'});});
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();vi.clearAllMocks();});
async function flush(){await act(async()=>{await Promise.resolve();});}
it('authenticates in the first frame and reloads state on ready and changes',async()=>{
 const {result}=renderHook(()=>useLiveEvents());await flush();const socket=Socket.all[0];
 act(()=>{socket.open();socket.event('ready');});
 expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ticket:'one-use-ticket'}));expect(socket.url).not.toContain('ticket=');
 expect(result.current).toBe('Live updates connected');expect(mocks.changed).toHaveBeenCalledTimes(1);
 act(()=>socket.event('conversation.updated'));expect(mocks.changed).toHaveBeenCalledTimes(2);
});
it('reconnects with a fresh ticket and recovers the authoritative state',async()=>{
 const {result,unmount}=renderHook(()=>useLiveEvents());await flush();
 act(()=>{Socket.all[0].open();Socket.all[0].event('ready');Socket.all[0].close();});
 expect(result.current).toContain('Reconnecting');await act(async()=>{await vi.advanceTimersByTimeAsync(1000);});
 expect(mocks.api).toHaveBeenCalledTimes(2);expect(Socket.all).toHaveLength(2);
 act(()=>{Socket.all[1].open();Socket.all[1].event('ready');});expect(mocks.changed).toHaveBeenCalledTimes(2);
 unmount();await act(async()=>{await vi.advanceTimersByTimeAsync(30000);});expect(Socket.all).toHaveLength(2);
});
it('returns to login when the server revokes the session',async()=>{
 renderHook(()=>useLiveEvents());await flush();act(()=>Socket.all[0].onclose?.({code:4401}));expect(mocks.clear).toHaveBeenCalledOnce();
 await act(async()=>{await vi.advanceTimersByTimeAsync(30000);});expect(Socket.all).toHaveLength(1);
});
it('detects a silent broken connection using its heartbeat deadline',async()=>{
 const {result}=renderHook(()=>useLiveEvents());await flush();act(()=>{Socket.all[0].open();Socket.all[0].event('ready');});
 await act(async()=>{await vi.advanceTimersByTimeAsync(20000);});expect(result.current).toContain('Reconnecting');
});
