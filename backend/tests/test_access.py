"""Access checks run without the fixture's explicit authenticated test override."""
import time
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app,get_retriever
from app.llm import get_generator
from app.config import settings
from app.access import require_access,allow_chat,signer,reserve
from app.models import Conversation,Message,Ticket,RequestBudget

@pytest.fixture
def secured(client,monkeypatch):
    monkeypatch.setattr(settings(),'review_password','test-review-password-2026')
    monkeypatch.setattr(settings(),'session_secret','test-session-signing-secret-32-characters-long')
    app.dependency_overrides.pop(require_access)
    app.dependency_overrides.pop(allow_chat)
    return client

def token(client):
    response=client.post('/api/auth/session',json={'password':'test-review-password-2026'})
    assert response.status_code==200
    return {'Authorization':'Bearer '+response.json()['access_token']}

def test_public_chat_and_history_require_authentication_before_provider(secured,database):
    def forbidden(*args):raise AssertionError('Unauthenticated request reached retrieval')
    app.dependency_overrides[get_retriever]=lambda:forbidden
    assert secured.post('/api/chat',json={'message':'ID card cost?'}).status_code==401
    assert secured.get('/api/conversations/unknown').status_code==401
    assert secured.post('/api/conversations/unknown/escalate',json={'message_id':'00000000-0000-0000-0000-000000000000','confirmed':True}).status_code==401
    assert secured.get('/api/health').status_code==200
    with Session(database) as db:
        assert not db.scalars(select(Conversation)).all()
        assert not db.scalars(select(RequestBudget)).all()

def test_missing_configuration_fails_closed(client,monkeypatch):
    app.dependency_overrides.pop(require_access)
    app.dependency_overrides.pop(allow_chat)
    monkeypatch.setattr(settings(),'review_password','')
    monkeypatch.setattr(settings(),'session_secret','')
    assert client.post('/api/chat',json={'message':'hi'}).status_code==503
    assert client.post('/api/auth/session',json={'password':'anything'}).status_code==503

def test_bad_password_and_tampered_or_expired_tokens_are_denied(secured,monkeypatch):
    assert secured.post('/api/auth/session',json={'password':'wrong'}).status_code==401
    valid=token(secured)
    assert secured.get('/api/auth/session',headers=valid).status_code==200
    assert secured.post('/api/chat',json={'message':'hi'},headers={'Authorization':valid['Authorization']+'tampered'}).status_code==401
    with monkeypatch.context() as m:
        m.setattr('itsdangerous.timed.TimestampSigner.get_timestamp',lambda self:int(time.time())-40000)
        expired=signer().dumps({'session':'a'*64})
    assert secured.get('/api/auth/session',headers={'Authorization':'Bearer '+expired}).status_code==401
    monkeypatch.setattr(settings(),'session_secret','rotated-secret-32-characters-long-for-tests')
    assert secured.get('/api/auth/session',headers=valid).status_code==401

def test_login_attempts_are_limited_and_forwarded_headers_do_not_bypass(secured):
    for i in range(5):
        assert secured.post('/api/auth/session',json={'password':'wrong'},headers={'X-Forwarded-For':f'192.0.2.{i}'}).status_code==401
    response=secured.post('/api/auth/session',json={'password':'test-review-password-2026'})
    assert response.status_code==429 and int(response.headers['retry-after'])>0

def test_sessions_cannot_read_continue_or_escalate_each_others_conversations(secured,database):
    first=token(secured);second=token(secured)
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    answer=secured.post('/api/chat',json={'message':'Where is my private timetable?'},headers=first).json()
    path='/api/conversations/'+answer['conversation_id']
    assert secured.get(path,headers=first).status_code==200
    assert secured.get(path,headers=second).status_code==404
    assert secured.post('/api/chat',json={'message':'yes please','conversation_id':answer['conversation_id']},headers=second).status_code==404
    assert secured.post(path+'/escalate',json={'message_id':answer['user_message_id'],'confirmed':True},headers=second).status_code==404
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

@pytest.mark.parametrize('setting',['chat_requests_per_minute','chat_requests_per_day','session_requests_per_minute','session_requests_per_day'])
def test_request_limits_block_chat(secured,monkeypatch,setting):
    monkeypatch.setattr(settings(),setting,1)
    headers=token(secured)
    assert secured.post('/api/chat',json={'message':'hi'},headers=headers).status_code==200
    response=secured.post('/api/chat',json={'message':'hi'},headers=headers)
    assert response.status_code==429 and 'Retry-After' in response.headers

def test_global_limit_cannot_be_reset_by_logging_in_again(secured,monkeypatch):
    monkeypatch.setattr(settings(),'chat_requests_per_day',1)
    assert secured.post('/api/chat',json={'message':'hi'},headers=token(secured)).status_code==200
    assert secured.post('/api/chat',json={'message':'hi'},headers=token(secured)).status_code==429

def test_provider_failure_still_consumes_persistent_budget(secured,database,monkeypatch,source):
    monkeypatch.setattr(settings(),'chat_requests_per_day',1)
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[source]
    class Broken:
        def generate(self,*args):raise HTTPException(502,'Test provider failure')
    app.dependency_overrides[get_generator]=lambda:Broken()
    headers=token(secured)
    assert secured.post('/api/chat',json={'message':'Robotics hours?'},headers=headers).status_code==502
    assert secured.post('/api/chat',json={'message':'Robotics hours?'},headers=headers).status_code==429
    with Session(database) as db:
        assert not db.scalars(select(Message)).all()
        assert db.scalar(select(RequestBudget.count).where(RequestBudget.key=='chat:global:day'))==1

def test_paused_chat_never_reaches_model(secured,monkeypatch):
    monkeypatch.setattr(settings(),'chat_enabled',False)
    response=secured.post('/api/chat',json={'message':'hi'},headers=token(secured))
    assert response.status_code==503 and 'paused' in response.json()['detail']

def test_budget_survives_new_database_sessions(database):
    with Session(database) as db:reserve(db,[('test-budget',86400,1)])
    with Session(database) as db:
        with pytest.raises(HTTPException) as error:reserve(db,[('test-budget',86400,1)])
    assert error.value.status_code==429

def test_budget_database_failure_blocks_chat_before_retrieval(secured,monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    headers=token(secured)
    def broken(*args,**kwargs):raise SQLAlchemyError('Test budget storage unavailable')
    monkeypatch.setattr(Session,'execute',broken)
    response=secured.post('/api/chat',json={'message':'ID card cost?'},headers=headers)
    assert response.status_code==503

def test_legacy_unowned_conversations_are_not_claimed_by_new_sessions(secured,database):
    with Session(database) as db:
        legacy=Conversation();db.add(legacy);db.commit();cid=legacy.id
    headers=token(secured)
    assert secured.get('/api/conversations/'+cid,headers=headers).status_code==404
    assert secured.post('/api/chat',json={'message':'hello','conversation_id':cid},headers=headers).status_code==404
