"""Account authentication with opaque, revocable server-side sessions."""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import RequestBudget, User, LoginSession, now

COOKIE = 'campus_session'
hasher = PasswordHasher()
# Equal password-verification work for unknown usernames.
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))

class AccessLogin(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)

def digest(token: str):
    return hashlib.sha256(token.encode()).hexdigest()

def unexpired(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value > now()

def session_user(token: str | None, db: Session):
    session = db.get(LoginSession, digest(token)) if token else None
    if not session or not unexpired(session.expires_at):
        raise HTTPException(401, 'Your session has expired. Please sign in again.')
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, 'Please sign in again.')
    return user

def require_user(request: Request, db: Session = Depends(get_db)):
    return session_user(request.cookies.get(COOKIE), db)

def require_access(user: User = Depends(require_user)):
    if user.role != 'student':
        raise HTTPException(403, 'Student access is required.')
    return user.id

def staff(user: User = Depends(require_user)):
    if user.role != 'staff':
        raise HTTPException(403, 'Staff access is required.')
    return user

def public_user(user):
    return {'id': user.id, 'username': user.username, 'role': user.role}

def reserve(db: Session, buckets: list[tuple[str,int,int]]):
    """Atomically reserve all counters before work; retries/failures still count.

    Counters commit before provider calls, surviving rollbacks and restarts.
    Conditional upserts enforce the limit across concurrent API workers.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert=pg_insert if db.bind.dialect.name=='postgresql' else sqlite_insert
    current=int(time.time())
    try:
        db.execute(delete(RequestBudget).where(RequestBudget.window<current-172800))
        for key,seconds,limit in buckets:
            window=current//seconds*seconds
            if limit<1:
                raise HTTPException(429,'The helpdesk request limit has been reached. Please try again later.',headers={'Retry-After':str(window+seconds-current)})
            stmt=insert(RequestBudget).values(key=key,window=window,count=1)
            stmt=stmt.on_conflict_do_update(index_elements=['key','window'],set_={'count':RequestBudget.count+1},where=RequestBudget.count<limit).returning(RequestBudget.count)
            if db.scalar(stmt) is None:
                raise HTTPException(429,'The helpdesk request limit has been reached. Please try again later.',headers={'Retry-After':str(window+seconds-current)})
        db.commit()
    except Exception:
        db.rollback()
        raise

def login(body: AccessLogin, request: Request, response: Response, db: Session):
    peer = digest(request.client.host if request.client else 'unknown')
    reserve(db, [('login:global', 60, 30), ('login:' + peer, 60, 5)])
    user = db.scalar(select(User).where(User.username == body.username.strip()))
    try:
        valid = hasher.verify(user.password_hash if user else DUMMY_HASH, body.password)
    except (VerificationError, InvalidHashError):
        valid = False
    if not valid or not user:
        raise HTTPException(401, 'Incorrect username or password.')
    token = secrets.token_urlsafe(48)
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= now()))
    db.add(LoginSession(token_hash=digest(token), user_id=user.id,
                        expires_at=now() + timedelta(seconds=settings().session_max_age)))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=settings().session_max_age,
                        httponly=True, secure=settings().cookie_secure, samesite='lax', path='/api')
    response.headers['Cache-Control'] = 'no-store'
    return public_user(user)

def logout(request: Request, response: Response, db: Session):
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(token)))
        db.commit()
    response.delete_cookie(COOKIE, path='/api', secure=settings().cookie_secure, httponly=True, samesite='lax')
    return {'authenticated': False}

def allow_chat(owner: str = Depends(require_access)):
    # Capacity is reserved only for new AI work, after retry/state checks.
    if not settings().chat_enabled:
        raise HTTPException(503, 'Chat is temporarily paused by the project owner.')
    return owner

def reserve_ai(db, owner):
    config = settings()
    reserve(db, [('chat:global:minute',60,config.chat_requests_per_minute),
                 ('chat:global:day',86400,config.chat_requests_per_day),
                 ('chat:account:minute:'+owner,60,config.session_requests_per_minute),
                 ('chat:account:day:'+owner,86400,config.session_requests_per_day)])
