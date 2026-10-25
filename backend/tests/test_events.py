from datetime import timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect
from app.events import consume_ticket,hub
from app.models import LoginSession,WebSocketTicket,now
from app.access import digest
from app.main import app,get_retriever
STUDENT={'Cookie':'campus_session=test-student-token'}
STAFF={'Cookie':'campus_session=test-staff-token'}
ORIGIN={'Origin':'http://localhost:5173'}

def ticket(client,headers=None):
    result=client.post('/api/auth/ws-ticket',headers=headers or STUDENT)
    assert result.status_code==200,result.text
    return result.json()['ticket']

def connect(client,token):
    manager=client.websocket_connect('/api/events',headers=ORIGIN)
    socket=manager.__enter__()
    socket.send_json({'ticket':token})
    assert socket.receive_json()=={'type':'ready'}
    return manager,socket


def test_socket_tickets_are_hashed_single_use_and_expiring(client,database):
    raw=ticket(client)
    with Session(database) as db:
        assert db.get(WebSocketTicket,raw) is None
        assert db.get(WebSocketTicket,digest(raw)) is not None
    assert consume_ticket(database,raw)['role']=='student'
    assert consume_ticket(database,raw) is None
    expired=ticket(client)
    with Session(database) as db:
        db.get(WebSocketTicket,digest(expired)).expires_at=now()-timedelta(seconds=1);db.commit()
    assert consume_ticket(database,expired) is None


def test_websocket_rejects_bad_origin_missing_and_reused_tickets(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/api/events',headers={'Origin':'https://attacker.example'}):pass
    with client.websocket_connect('/api/events',headers=ORIGIN) as socket:
        socket.send_json({'ticket':'invalid-ticket-with-enough-length'})
        with pytest.raises(WebSocketDisconnect):socket.receive_json()
    raw=ticket(client)
    manager,socket=connect(client,raw)
    try:
        with client.websocket_connect('/api/events',headers=ORIGIN) as second:
            second.send_json({'ticket':raw})
            with pytest.raises(WebSocketDisconnect):second.receive_json()
    finally:manager.__exit__(None,None,None)


def test_committed_updates_reach_student_and_staff_with_reconnect_recovery(client,database):
    cid=str(uuid4());client.post('/api/conversations',json={'id':cid})
    manager,student=connect(client,ticket(client))
    staff_manager,staff=connect(client,ticket(client,STAFF))
    try:
        app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
        result=client.post(f'/api/conversations/{cid}/messages',json={'message':'Private timetable?','client_request_id':str(uuid4())}).json()
        assert student.receive_json()=={'type':'conversation.updated','conversation_id':cid}
        mid=result['messages'][-1]['ticket_offer']['message_id']
        client.post(f'/api/conversations/{cid}/escalate',json={'message_id':mid,'confirmed':True})
        assert student.receive_json()['conversation_id']==cid
        assert staff.receive_json()['conversation_id']==cid
        client.post(f'/api/conversations/{cid}/accept',headers=STAFF)
        assert student.receive_json()['conversation_id']==cid
        assert staff.receive_json()['conversation_id']==cid
        body={'message':'A live staff response','client_request_id':str(uuid4())}
        sent=client.post(f'/api/conversations/{cid}/messages',headers=STAFF,json=body)
        assert sent.status_code==200
        assert student.receive_json()['conversation_id']==cid
        assert staff.receive_json()['conversation_id']==cid
    finally:
        manager.__exit__(None,None,None);staff_manager.__exit__(None,None,None)
    # Connection registry is disposable; the full persisted reply survives reconnect.
    manager,student=connect(client,ticket(client))
    try:
        transcript=client.get('/api/conversations/'+cid).json()
        assert transcript['messages'][-1]['content']=='A live staff response'
        assert transcript['messages'][-1]['role']=='staff'
    finally:manager.__exit__(None,None,None)


def test_logout_closes_active_socket_and_revokes_unused_ticket(client):
    raw=ticket(client)
    spare=ticket(client)
    manager,socket=connect(client,raw)
    try:
        assert client.delete('/api/auth/session',headers=STUDENT).status_code==200
        with pytest.raises(WebSocketDisconnect) as error:socket.receive_json()
        assert error.value.code==4401
        with client.websocket_connect('/api/events',headers=ORIGIN) as second:
            second.send_json({'ticket':spare})
            with pytest.raises(WebSocketDisconnect):second.receive_json()
    finally:manager.__exit__(None,None,None)


def test_failed_commit_does_not_broadcast(client,database,monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    cid=str(uuid4());client.post('/api/conversations',json={'id':cid})
    notifications=[]
    monkeypatch.setattr(hub,'changed',lambda *args:notifications.append(args))
    original=Session.commit
    def fail_transcript(db):
        from app.models import Message
        if db.scalar(select(Message.id).where(Message.conversation_id==cid).limit(1)):
            raise SQLAlchemyError('Controlled commit failure')
        return original(db)
    monkeypatch.setattr(Session,'commit',fail_transcript)
    result=client.post(f'/api/conversations/{cid}/messages',json={'message':'hello','client_request_id':str(uuid4())})
    assert result.status_code==503
    assert notifications==[]
    assert client.get('/api/conversations/'+cid).json()['messages']==[]

def test_expired_session_cannot_receive_committed_updates(client,database):
    manager,socket=connect(client,ticket(client))
    try:
        with Session(database) as db:
            db.get(LoginSession,digest('test-student-token')).expires_at=now()-timedelta(seconds=1)
            db.commit()
        hub.changed(str(uuid4()),'test-owner',False)
        with pytest.raises(WebSocketDisconnect) as error:socket.receive_json()
        assert error.value.code==4401
    finally:manager.__exit__(None,None,None)
