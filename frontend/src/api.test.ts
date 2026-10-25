import { afterEach, expect, it, vi } from 'vitest';
import { api } from './api';
afterEach(()=>vi.unstubAllGlobals());
it('uses the same-origin proxy and cookie credentials',async()=>{
 const request=vi.fn().mockResolvedValue({ok:true,json:async()=>({})});vi.stubGlobal('fetch',request);
 await api('/chat',{method:'POST',body:'{}'});
 expect(request).toHaveBeenCalledWith('/api/chat',expect.objectContaining({credentials:'same-origin',headers:{'Content-Type':'application/json'}}));
});
it('reports a network error without simulating success',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('offline')));await expect(api('/chat',{method:'POST'})).rejects.toThrow('Could not reach');
});
it('expires the UI when a WebSocket-ticket request rejects the session',async()=>{
 const expired=vi.fn();window.addEventListener('campus-access-expired',expired);
 try{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:401,json:async()=>({detail:'Please sign in again.'})}));
  await expect(api('/auth/ws-ticket',{method:'POST'})).rejects.toThrow('Please sign in');expect(expired).toHaveBeenCalledOnce();
 }finally{window.removeEventListener('campus-access-expired',expired);}
});
