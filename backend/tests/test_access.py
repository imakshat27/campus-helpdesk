"""Access checks run without the fixture's explicit authenticated test override."""
import time
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app,get_retriever
from app.llm import get_generator
from app.config import settings
from app.access import require_access,allow_chat,reserve,COOKIE,digest
from app.models import Conversation,Message,Ticket,RequestBudget,LoginSession,now
from datetime import timedelta

@pytest.fixture
def secured(client,monkeypatch):
    client.headers.pop('Cookie',None)
    app.dependency_overrides.pop(require_access)
    app.dependency_overrides.pop(allow_chat)
    return client

def token(client):
    response=client.post('/api/auth/session',json={'username':'test-student','password':'test-student-password-long'})
    assert response.status_code==200
    cookie=client.cookies.get(COOKIE)
    client.cookies.clear()
    return {'Cookie': COOKIE+'='+cookie}

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

def test_unprovisioned_account_cannot_login(secured):
    assert secured.post('/api/auth/session',json={'username':'unknown','password':'anything'}).status_code==401


def test_bad_password_tampering_expiry_and_logout(secured,database):
    assert secured.post('/api/auth/session',json={'username':'test-student','password':'wrong'}).status_code==401
    valid=token(secured)
    assert secured.get('/api/auth/session',headers=valid).json()['role']=='student'
    assert secured.get('/api/auth/session',headers={'Cookie':valid['Cookie']+'tampered'}).status_code==401
    with Session(database) as db:
        row=db.get(LoginSession,digest(valid['Cookie'].split('=',1)[1]))
        row.expires_at=now()-timedelta(seconds=1);db.commit()
    assert secured.get('/api/auth/session',headers=valid).status_code==401
    valid=token(secured)
    assert secured.delete('/api/auth/session',headers=valid).status_code==200
    assert secured.get('/api/auth/session',headers=valid).status_code==401

def test_login_attempts_are_limited_and_forwarded_headers_do_not_bypass(secured):
    for i in range(5):
        assert secured.post('/api/auth/session',json={'username':'test-student','password':'wrong'},headers={'X-Forwarded-For':f'192.0.2.{i}'}).status_code==401
    response=secured.post('/api/auth/session',json={'username':'test-student','password':'test-student-password-long'})
    assert response.status_code==429 and int(response.headers['retry-after'])>0

def test_account_history_survives_new_login_and_foreign_owner_is_denied(secured,database):
    first=token(secured);second=token(secured)
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    answer=secured.post('/api/chat',json={'message':'Where is my private timetable?'},headers=first).json()
    path='/api/conversations/'+answer['conversation_id']
    assert secured.get(path,headers=first).status_code==200
    assert secured.get(path,headers=second).status_code==200
    with Session(database) as db:
        db.get(Conversation,answer['conversation_id']).owner='another-student';db.commit()
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

def test_origin_validation_and_cookie_attributes(secured,monkeypatch):
    body={'username':'test-student','password':'test-student-password-long'}
    assert secured.post('/api/auth/session',json=body,headers={'Origin':'https://attacker.example'}).status_code==403
    monkeypatch.setattr(settings(),'cookie_secure',True)
    response=secured.post('/api/auth/session',json=body)
    cookie=response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie and 'Max-Age=28800' in cookie
    assert 'access_token' not in response.json()


def test_student_cannot_use_staff_routes_and_staff_cannot_chat(secured):
    student=token(secured)
    assert secured.get('/api/staff/tickets',headers=student).status_code==403
    staff={'Cookie':COOKIE+'=test-staff-token'}
    assert secured.get('/api/staff/tickets',headers=staff).status_code==200
    assert secured.post('/api/chat',headers=staff,json={'message':'hi'}).status_code==403


def test_provisioning_is_idempotent_and_password_change_revokes_sessions(database):
    from types import SimpleNamespace
    from app.provision_accounts import provision
    from app.models import User
    config=SimpleNamespace(student_username='test-student',student_password='test-student-password-long',
                           staff_username='test-staff',staff_password='test-staff-password-long')
    with Session(database) as db:
        provision(db,config)
        ids={user.role:user.id for user in db.scalars(select(User)).all()}
        provision(db,config)
        assert {user.role:user.id for user in db.scalars(select(User)).all()}==ids
        assert db.get(LoginSession,digest('test-staff-token')) is not None
        config.staff_password='changed-staff-password-long'
        provision(db,config)
        assert db.get(LoginSession,digest('test-staff-token')) is None
