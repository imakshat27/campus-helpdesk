"""Single-worker live invalidation. Neon is the authoritative transcript.

Only committed changes produce events. Events contain identifiers, never message
content. Reconnecting clients reload authorized HTTP state instead of relying on
process-local event history. Add a shared broker before running multiple workers.
"""
import asyncio
import json
import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from .access import COOKIE, digest, require_user, reserve, unexpired
from .config import settings
from .db import engine, get_db
from .models import LoginSession, User, WebSocketTicket, Ticket, now

router=APIRouter()
AUTH_CHECK_SECONDS=5

class EventHub:
    def __init__(self):
        self.connections={}
        self.loop=None

    async def add(self,socket,principal):
        self.loop=asyncio.get_running_loop()
        if sum(p['session_hash']==principal['session_hash'] for p in self.connections.values())>=5:
            await socket.close(code=1013);return False
        self.connections[socket]=principal
        return True

    def remove(self,socket):
        self.connections.pop(socket,None)

    def schedule(self,coroutine):
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(lambda:asyncio.create_task(coroutine()))

    def changed(self,cid,owner,staff_visible):
        async def deliver():
            targets=[socket for socket,p in list(self.connections.items())
                     if p['user_id']==owner or (staff_visible and p['role']=='staff')]
            async def send(socket):
                try:
                    principal=self.connections.get(socket)
                    if not principal:return
                    if not await run_in_threadpool(active_session,principal['bind'],principal['session_hash']):
                        self.remove(socket);await socket.close(code=4401);return
                    await asyncio.wait_for(socket.send_json({'type':'conversation.updated','conversation_id':cid}),timeout=3)
                except Exception:
                    self.remove(socket)
                    try:await socket.close(code=1011)
                    except Exception:pass
            await asyncio.gather(*(send(socket) for socket in targets))
        self.schedule(deliver)

    def revoked(self,session_hash):
        async def close():
            for socket,p in list(self.connections.items()):
                if p['session_hash']==session_hash:
                    self.remove(socket)
                    try:await socket.close(code=4401)
                    except Exception:pass
        self.schedule(close)

hub=EventHub()

def commit_conversation(db,conversation):
    cid,owner=conversation.id,conversation.owner
    staff_visible=bool(db.scalar(select(Ticket.id).where(Ticket.conversation_id==cid).limit(1)))
    db.commit()
    hub.changed(cid,owner,staff_visible)

@router.post('/api/auth/ws-ticket')
def issue_ticket(request: Request,user=Depends(require_user),db: Session=Depends(get_db)):
    reserve(db,[('ws-ticket:'+user.id,60,30)])
    # Revalidate after the limiter commits: logout may have raced issuance.
    session_hash=digest(request.cookies.get(COOKIE,''))
    session=db.get(LoginSession,session_hash)
    if not session or not unexpired(session.expires_at):raise HTTPException(401,'Please sign in again.')
    token=secrets.token_urlsafe(32)
    db.execute(delete(WebSocketTicket).where(WebSocketTicket.expires_at<=now()))
    db.add(WebSocketTicket(token_hash=digest(token),session_hash=session_hash,expires_at=now()+timedelta(seconds=30)))
    db.commit()
    return {'ticket':token,'expires_in':30}

def get_event_engine():
    return engine()

def consume_ticket(bind,token):
    with Session(bind) as db:
        session_hash=db.scalar(delete(WebSocketTicket).where(WebSocketTicket.token_hash==digest(token),WebSocketTicket.expires_at>now()).returning(WebSocketTicket.session_hash))
        if not session_hash:return None
        session=db.get(LoginSession,session_hash)
        user=db.get(User,session.user_id) if session and unexpired(session.expires_at) else None
        db.commit()
        if not user:return None
        return {'session_hash':session_hash,'user_id':user.id,'role':user.role}

def active_session(bind,session_hash):
    with Session(bind) as db:
        session=db.get(LoginSession,session_hash)
        return bool(session and unexpired(session.expires_at))

@router.websocket('/api/events')
async def events(socket: WebSocket,bind=Depends(get_event_engine)):
    if socket.headers.get('origin') not in settings().cors_origins:
        await socket.close(code=1008);return
    await socket.accept()
    try:
        frame=await asyncio.wait_for(socket.receive_text(),timeout=5)
        if len(frame)>512:raise ValueError('Oversized authentication')
        payload=json.loads(frame)
        token=payload.get('ticket') if isinstance(payload,dict) else None
        if not isinstance(token,str) or not 20<=len(token)<=100:raise ValueError('Invalid authentication')
        principal=await run_in_threadpool(consume_ticket,bind,token)
        if not principal:
            await socket.close(code=4401);return
        principal['bind']=bind
        if not await hub.add(socket,principal):return
        await socket.send_json({'type':'ready'})
        while True:
            try:
                # The connection is server-to-client after authentication.
                await asyncio.wait_for(socket.receive_text(),timeout=AUTH_CHECK_SECONDS)
                await socket.close(code=1008);return
            except asyncio.TimeoutError:
                if not await run_in_threadpool(active_session,bind,principal['session_hash']):
                    await socket.close(code=4401);return
                await socket.send_json({'type':'heartbeat'})
    except WebSocketDisconnect:
        pass
    except (asyncio.TimeoutError,ValueError,TypeError,json.JSONDecodeError):
        await socket.close(code=4401)
    except Exception:
        # Do not include credentials or database diagnostics in socket frames.
        try:await socket.close(code=1011)
        except Exception:pass
    finally:
        hub.remove(socket)
