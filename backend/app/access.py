"""Private demo access. No frontend secret or process-local spend counter."""
import hashlib
import secrets
import time
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from itsdangerous import URLSafeTimedSerializer, BadSignature
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import RequestBudget

bearer=HTTPBearer(auto_error=False)

class AccessLogin(BaseModel):
    password: str = Field(min_length=1,max_length=1024)

def signer():
    config=settings()
    if len(config.review_password)<16 or len(config.session_secret)<32:
        raise HTTPException(503,'Private access is not configured. Contact the project owner.')
    return URLSafeTimedSerializer(config.session_secret,salt='campus-review-v1',signer_kwargs={'digest_method':hashlib.sha256})

def require_access(credentials: HTTPAuthorizationCredentials | None=Depends(bearer)):
    serializer=signer()  # Missing configuration always closes access.
    if not credentials:
        raise HTTPException(401,'Sign in to use the helpdesk.',headers={'WWW-Authenticate':'Bearer'})
    try:
        payload=serializer.loads(credentials.credentials,max_age=settings().session_max_age)
        if not isinstance(payload,dict) or not isinstance(payload.get('session'),str) or len(payload['session'])!=64:
            raise ValueError('Invalid session')
        return payload['session']
    except (BadSignature,ValueError,TypeError):
        raise HTTPException(401,'Your session has expired. Please sign in again.',headers={'WWW-Authenticate':'Bearer'}) from None

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

def login(body: AccessLogin, request: Request, db: Session):
    serializer=signer()
    # Use the server's client address, never an arbitrary forwarded header.
    peer=hashlib.sha256((request.client.host if request.client else 'unknown').encode()).hexdigest()
    reserve(db,[('login:global',60,30),('login:'+peer,60,5)])
    if not secrets.compare_digest(body.password.encode(),settings().review_password.encode()):
        raise HTTPException(401,'Incorrect access password.')
    token=serializer.dumps({'session':secrets.token_hex(32)})
    return {'access_token':token,'token_type':'bearer','expires_in':settings().session_max_age}

def allow_chat(owner: str=Depends(require_access),db: Session=Depends(get_db)):
    config=settings()
    if not config.chat_enabled:
        raise HTTPException(503,'Chat is temporarily paused by the project owner.')
    reserve(db,[('chat:global:minute',60,config.chat_requests_per_minute),
                ('chat:global:day',86400,config.chat_requests_per_day),
                ('chat:session:minute:'+owner,60,config.session_requests_per_minute),
                ('chat:session:day:'+owner,86400,config.session_requests_per_day)])
    return owner
