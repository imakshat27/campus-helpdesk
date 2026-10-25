import { useEffect, useState } from 'react';
import { api, conversationChanged } from '../api';
import { clearAccess } from '../access';

export function useLiveEvents(enabled=true) {
  const [status,setStatus]=useState('Connecting to live updates…');
  useEffect(()=>{
    if(!enabled)return;
    let stopped=false;
    let socket:WebSocket | null=null;
    let timer:ReturnType<typeof setTimeout> | undefined;
    let attempts=0;
    let connecting=false;
    let watchdog:ReturnType<typeof setTimeout> | undefined;
    const wsUrl=import.meta.env.VITE_WS_URL || (import.meta.env.DEV
      ? `ws://${window.location.hostname}:8000/api/events`
      : 'wss://campus-helpdesk-ye2a.onrender.com/api/events');
    function retry(){
      if(stopped)return;
      setStatus('Live updates disconnected · Reconnecting…');
      const delay=Math.min(1000*2**attempts++,30000);
      timer=setTimeout(()=>void connect(),delay);
    }
    function watch(){
      clearTimeout(watchdog);
      watchdog=setTimeout(()=>socket?.close(),20000);
    }
    async function connect(){
      if(stopped || connecting)return;
      connecting=true;
      try{
        const {ticket}=await api<{ticket:string}>('/auth/ws-ticket',{method:'POST'});
        if(stopped)return;
        socket=new WebSocket(wsUrl);
        socket.onopen=()=>{connecting=false;socket?.send(JSON.stringify({ticket}));watch();};
        socket.onmessage=event=>{
          try{
            const data=JSON.parse(event.data);
            if(data.type==='ready'){attempts=0;setStatus('Live updates connected');conversationChanged();watch();}
            else if(data.type==='heartbeat')watch();
            else if(data.type==='conversation.updated'){conversationChanged();watch();}
          }catch{/* Ignore malformed events; recovery always reloads HTTP state. */}
        };
        socket.onclose=event=>{
          connecting=false;clearTimeout(watchdog);
          if(stopped)return;
          if(event.code===4401){setStatus('Please sign in again.');clearAccess();return;}
          retry();
        };
        socket.onerror=()=>socket?.close();
      }catch{connecting=false;retry();}
    }
    function online(){clearTimeout(timer);if(!socket || socket.readyState===WebSocket.CLOSED)void connect();}
    void connect();window.addEventListener('online',online);
    return()=>{stopped=true;clearTimeout(timer);clearTimeout(watchdog);window.removeEventListener('online',online);socket?.close();};
  },[enabled]);
  return status;
}
