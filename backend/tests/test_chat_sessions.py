from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app,get_retriever
from app.llm import get_generator
from app.models import Conversation,Message,Ticket,Submission
STAFF={'Cookie':'campus_session=test-staff-token'}

def create(client):
    cid=str(uuid4())
    response=client.post('/api/conversations',json={'id':cid})
    assert response.status_code==200,response.text
    return cid

def send(client,cid,message,key=None,headers=None):
    return client.post(f'/api/conversations/{cid}/messages',json={'message':message,'client_request_id':key or str(uuid4())},headers=headers)

def handoff(client,cid):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    response=send(client,cid,'What is my private timetable?')
    assert response.status_code==200,response.text
    last=response.json()['messages'][-1]
    assert last['outcome']=='needs_staff_confirmation'
    target=last['ticket_offer']['message_id']
    response=client.post(f'/api/conversations/{cid}/escalate',json={'message_id':target,'confirmed':True})
    assert response.status_code==200,response.text
    return target,response.json()['ticket_reference']

def test_history_is_account_owned_and_conversation_context_is_separate(client,database):
    first=create(client);second=create(client)
    send(client,first,'hello');send(client,second,'thanks')
    history=client.get('/api/conversations').json()
    assert {c['id'] for c in history}=={first,second}
    assert client.get('/api/conversations/'+first).json()['messages'][0]['content']=='hello'
    assert client.get('/api/conversations/'+second).json()['messages'][0]['content']=='thanks'
    with Session(database) as db:
        db.get(Conversation,first).owner='someone-else';db.commit()
    assert client.get('/api/conversations/'+first).status_code==404
    assert client.get('/api/conversations/'+second,headers=STAFF).status_code==404


def test_complete_staff_takeover_and_reopen(client,database):
    cid=create(client);target,reference=handoff(client,cid)
    def forbidden(*args):raise AssertionError('AI ran during staff takeover')
    app.dependency_overrides[get_retriever]=lambda:forbidden
    data=send(client,cid,'Additional details while waiting').json()
    assert data['state']=='waiting_for_staff' and data['messages'][-1]['content']=='Additional details while waiting'
    assert send(client,cid,'Staff reply too soon',headers=STAFF).status_code==409
    assert client.post(f'/api/conversations/{cid}/accept',headers=STAFF).json()['state']=='staff_active'
    data=send(client,cid,'I can help you with this.',headers=STAFF).json()
    assert data['messages'][-1]['role']=='staff' and data['messages'][-1]['sender_id']=='test-staff'
    data=send(client,cid,'Thank you, here is another detail').json()
    assert data['messages'][-1]['role']=='user'
    tickets=client.get('/api/staff/tickets',headers=STAFF).json()
    assert len(tickets)==1 and tickets[0]['reference']==reference and tickets[0]['conversation_id']==cid
    tid=tickets[0]['id']
    assert client.patch('/api/staff/tickets/'+tid,headers=STAFF,json={'status':'resolved'}).status_code==200
    assert send(client,cid,'closed').status_code==409
    assert send(client,cid,'closed staff',headers=STAFF).status_code==409
    assert client.post(f'/api/conversations/{cid}/reopen').json()['state']=='waiting_for_staff'
    with Session(database) as db:
        rows=db.scalars(select(Ticket).where(Ticket.conversation_id==cid)).all()
        assert len(rows)==1 and rows[0].message_id==target and rows[0].status=='open'


def test_idempotent_messages_and_request_id_conflicts(client,database):
    cid=create(client);key=str(uuid4())
    first=send(client,cid,'hello',key).json()
    second=send(client,cid,'hello',key).json()
    assert first==second and len(second['messages'])==2
    assert first['created_at'].endswith('+00:00') and first['messages'][0]['created_at'].endswith('+00:00')
    assert send(client,cid,'different content',key).status_code==409
    other=create(client)
    assert send(client,other,'hello',key).status_code==409
    with Session(database) as db:
        assert len(db.scalars(select(Submission)).all())==1
        assert [m.sequence for m in db.scalars(select(Message).where(Message.conversation_id==cid).order_by(Message.sequence))]==[1,2]


def test_staff_retries_and_duplicate_handoffs_preserve_state(client,database):
    cid=create(client);target,_=handoff(client,cid)
    client.post(f'/api/conversations/{cid}/accept',headers=STAFF)
    repeated=client.post(f'/api/conversations/{cid}/escalate',json={'message_id':target,'confirmed':True})
    assert repeated.status_code==200
    assert client.get('/api/conversations/'+cid).json()['state']=='staff_active'
    key=str(uuid4())
    first=send(client,cid,'Confirmed staff reply',key,STAFF).json()
    second=send(client,cid,'Confirmed staff reply',key,STAFF).json()
    assert first==second
    with Session(database) as db:
        assert len(db.scalars(select(Ticket).where(Ticket.conversation_id==cid)).all())==1
        assert len(db.scalars(select(Message).where(Message.role=='staff')).all())==1


def test_legacy_records_remain_staff_only(client,database):
    with Session(database) as db:
        legacy=Conversation(owner='old-anonymous-session',state='waiting_for_staff');db.add(legacy);db.flush()
        db.add(Ticket(conversation_id=legacy.id,reference='HD-LEGACY',query='Legacy question',reason='Previously confirmed'))
        db.commit();cid=legacy.id
    assert client.get('/api/conversations/'+cid).status_code==404
    assert client.get('/api/conversations/'+cid,headers=STAFF).status_code==200
    assert all(c['id']!=cid for c in client.get('/api/conversations').json())

def test_repeated_status_updates_do_not_reset_active_chat(client,database):
    cid=create(client);handoff(client,cid)
    client.post(f'/api/conversations/{cid}/accept',headers=STAFF)
    tid=client.get('/api/staff/tickets',headers=STAFF).json()[0]['id']
    assert client.patch('/api/staff/tickets/'+tid,headers=STAFF,json={'status':'open'}).status_code==200
    assert client.get('/api/conversations/'+cid).json()['state']=='staff_active'
    with Session(database) as db:
        db.add(Ticket(conversation_id=cid,reference='HD-OLDER-RESOLVED',query='Older question',reason='Historical',status='resolved'))
        db.commit()
        old=db.scalar(select(Ticket).where(Ticket.reference=='HD-OLDER-RESOLVED')).id
    assert client.patch('/api/staff/tickets/'+old,headers=STAFF,json={'status':'resolved'}).status_code==200
    assert client.get('/api/conversations/'+cid).json()['state']=='staff_active'
