from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from app.main import app, get_retriever
from app.db import get_db
from app.llm import get_generator, get_query_resolver, OpenRouterGenerator, ResolvedQuery
from app.models import Message, Ticket, Conversation, Document
from app.schemas import Generation
from app.config import settings

AUTH=('test-staff','test-password')

def test_grounded_answer_and_persistence(grounded,database):
    r=grounded.post('/api/chat',json={'message':'When does the robotics lab close?'})
    assert r.status_code==200
    result=r.json()
    assert result['outcome']=='answered'
    assert result['sources'][0]['title']=='Robotics lab hours'
    with Session(database) as db:
        assert len(db.scalars(select(Message)).all())==2
        assert db.get(Conversation,result['conversation_id'])
        assert not db.scalars(select(Ticket)).all()

def test_unsupported_asks_before_creating_ticket(client,database):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    result=client.post('/api/chat',json={'message':'What is my exam score?'}).json()
    assert result['outcome']=='needs_staff_confirmation'
    assert not result['ticket_reference'] and result['ticket_offer']['query']=='What is my exam score?'
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()
    url='/api/conversations/'+result['conversation_id']+'/escalate'
    assert client.post(url).status_code==422
    assert client.post(url,json={'message_id':result['user_message_id'],'confirmed':False}).status_code==422
    confirmed=client.post(url,json={'message_id':result['user_message_id'],'confirmed':True}).json()
    with Session(database) as db:
        assert db.scalar(select(Ticket)).reference==confirmed['ticket_reference']
    queue=client.get('/api/staff/tickets',auth=AUTH).json()
    assert queue[0]['messages'][0]['role']=='user'
    assert queue[0]['query']=='What is my exam score?'
    assert client.patch('/api/staff/tickets/'+queue[0]['id'],auth=AUTH,json={'status':'resolved'}).status_code==200
    assert client.get('/api/staff/tickets',auth=AUTH).json()==[]
    assert len(client.get('/api/staff/tickets?status=resolved',auth=AUTH).json())==1

def test_clarification_and_followup(grounded,database,source):
    class Generator:
        def generate(self,q,s,h):
            if not h:
                return Generation(outcome='clarification',message='Which lab do you mean: Robotics, Computer, or Chemistry?',source_ids=[])
            assert h[-1]['role']=='assistant' and 'Which lab' in h[-1]['content']
            return Generation(outcome='answered',message=source.content,source_ids=[source.id])
    app.dependency_overrides[get_generator]=lambda:Generator()
    first=grounded.post('/api/chat',json={'message':'When does the lab open?'}).json()
    assert first['outcome']=='clarification' and not first['ticket_reference']
    second=grounded.post('/api/chat',json={'message':'Robotics','conversation_id':first['conversation_id']}).json()
    assert second['outcome']=='answered'
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_invalid_source_rejected(grounded,database):
    class Bad:
        def generate(self,*args):
            return Generation(outcome='answered',message='An invented answer.',source_ids=['not-retrieved'])
    app.dependency_overrides[get_generator]=lambda:Bad()
    r=grounded.post('/api/chat',json={'message':'Lab hours?'})
    assert r.status_code==502
    with Session(database) as db:
        assert not db.scalars(select(Message)).all()
        assert not db.scalars(select(Conversation)).all()

def test_missing_citation_rejected(grounded):
    class Bad:
        def generate(self,*args):
            return Generation(outcome='answered',message='No evidence.',source_ids=[])
    app.dependency_overrides[get_generator]=lambda:Bad()
    assert grounded.post('/api/chat',json={'message':'Lab hours?'}).status_code==502

def test_provider_failure_is_not_missing_knowledge(grounded,database):
    class Down:
        def generate(self,*args):
            raise HTTPException(502,'The answer service could not complete this request. Please try again.')
    app.dependency_overrides[get_generator]=lambda:Down()
    assert grounded.post('/api/chat',json={'message':'Robotics lab hours?'}).status_code==502
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_database_failure_never_claims_ticket_saved(client):
    def broken():
        raise OperationalError('SELECT 1',{},Exception('offline'))
        yield
    app.dependency_overrides[get_db]=broken
    r=client.post('/api/chat',json={'message':'Help me'})
    assert r.status_code==503
    assert 'Nothing has been confirmed as saved' in r.json()['detail']

def test_failed_commit_does_not_confirm_handoff(client,database,monkeypatch):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    def fail(*args):
        raise OperationalError('COMMIT',{},Exception('connection lost'))
    monkeypatch.setattr(Session,'commit',fail)
    result=client.post('/api/chat',json={'message':'Missing policy?'})
    assert result.status_code==503 and 'ticket_reference' not in result.json()
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_staff_auth_and_invalid_updates(client):
    assert client.get('/api/staff/tickets').status_code==401
    assert client.get('/api/staff/tickets',auth=('wrong','wrong')).status_code==401
    assert client.get('/api/staff/tickets',auth=AUTH).status_code==200
    assert client.patch('/api/staff/tickets/missing',auth=AUTH,json={'status':'invalid'}).status_code==422
    assert client.patch('/api/staff/tickets/missing',auth=AUTH,json={'status':'resolved'}).status_code==404

def test_unconfigured_staff_has_no_default_access(client,monkeypatch):
    monkeypatch.setattr(settings(),'staff_password','')
    assert client.get('/api/staff/tickets',auth=AUTH).status_code==503

def test_search_and_unapproved_documents(client,database):
    assert len(client.get('/api/knowledge').json())==29
    docs=client.get('/api/knowledge?q=robotics&category=labs').json()
    assert docs and all(d['category']=='labs' for d in docs)
    with Session(database) as db:
        d=db.get(Document,'faq-05'); d.approved=False; db.commit()
    assert client.get('/api/knowledge/faq-05').status_code==404
    assert all(d['id']!='faq-05' for d in client.get('/api/knowledge').json())

def test_manual_handoff_is_idempotent(grounded):
    result=grounded.post('/api/chat',json={'message':'Robotics hours?'}).json()
    url='/api/conversations/'+result['conversation_id']+'/escalate'
    body={'message_id':result['user_message_id'],'confirmed':True}
    one=grounded.post(url,json=body).json(); two=grounded.post(url,json=body).json()
    assert one==two
    assert len(grounded.get('/api/staff/tickets',auth=AUTH).json())==1

def test_input_validation(client):
    for message in ['', '   ', 'a'*2001]:
        assert client.post('/api/chat',json={'message':message}).status_code==422
    assert client.post('/api/chat',json={'message':'hello','conversation_id':'not-a-uuid'}).status_code==422
    assert client.post('/api/chat',json={'message':'hello','conversation_id':'00000000-0000-0000-0000-000000000000'}).status_code==404

def test_openrouter_transport_and_invalid_output(monkeypatch,source):
    import httpx
    monkeypatch.setattr(settings(),'openrouter_api_key','fixture-key')
    monkeypatch.setattr(settings(),'openrouter_model','fixture-model')
    def fail(*args,**kwargs):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx.Client,'post',fail)
    import pytest
    with pytest.raises(HTTPException) as exc:
        OpenRouterGenerator().generate('lab hours',[source],[])
    assert exc.value.status_code==502

def test_unnamed_event_never_guesses_even_if_model_would(grounded,source,database):
    class MustNotRun:
        def generate(self,*args):
            raise AssertionError('The model must not choose an unnamed event')
    app.dependency_overrides[get_generator]=lambda:MustNotRun()
    result=grounded.post('/api/chat',json={'message':'How do I register for the event?'}).json()
    assert result['outcome']=='clarification'
    assert 'Which event' in result['message'] and not result['ticket_reference']
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_typed_consent_keeps_original_question(client,database):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    first=client.post('/api/chat',json={'message':'Is there a shuttle to the airport?'}).json()
    yes=client.post('/api/chat',json={'message':'yes please','conversation_id':first['conversation_id']}).json()
    assert yes['outcome']=='escalated' and yes['ticket_reference']
    with Session(database) as db:
        tickets=db.scalars(select(Ticket)).all()
        assert len(tickets)==1 and tickets[0].query=='Is there a shuttle to the airport?'

def test_declining_never_creates_ticket(client,database):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    first=client.post('/api/chat',json={'message':'A missing policy?'}).json()
    no=client.post('/api/chat',json={'message':'No thanks','conversation_id':first['conversation_id']}).json()
    assert no['outcome']=='conversation' and not no['ticket_reference']
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_greetings_and_thanks_do_not_require_sources_or_tickets(client,database):
    def must_not_search(*args):raise AssertionError('No campus search for greetings')
    app.dependency_overrides[get_retriever]=lambda:must_not_search
    first=client.post('/api/chat',json={'message':'hello'}).json()
    assert first['outcome']=='conversation'
    second=client.post('/api/chat',json={'message':'thanks','conversation_id':first['conversation_id']}).json()
    assert second['outcome']=='conversation'
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_long_followup_resolves_before_search(grounded,source):
    first=grounded.post('/api/chat',json={'message':'How do I replace a lost student ID?'}).json()
    class Resolver:
        def resolve(self,q,history):
            assert q=='so how much do i pay?'
            assert history[-2]['content']=='How do I replace a lost student ID?'
            assert history[-1]['role']=='assistant'
            return ResolvedQuery(query='What is the replacement fee for a lost student ID?',uses_context=True)
    searched=[]
    def search(db,q):
        searched.append(q);return [source]
    app.dependency_overrides[get_query_resolver]=lambda:Resolver()
    app.dependency_overrides[get_retriever]=lambda:search
    second=grounded.post('/api/chat',json={'message':'so how much do i pay?','conversation_id':first['conversation_id']}).json()
    assert second['outcome']=='answered'
    assert searched==['What is the replacement fee for a lost student ID?']

def test_prior_approved_passage_survives_empty_followup_retrieval(client,database):
    from app.models import Chunk
    from app.schemas import Source
    with Session(database) as db:
        d=db.get(Document,'faq-14')
        db.add(Chunk(id='faq-14:0',document_id=d.id,heading=d.title,content=d.content,embedding=[1.0]+[0.0]*383));db.commit()
        source=Source(id='faq-14:0',document_id=d.id,title=d.title,heading=d.title,content=d.content)
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[source]
    class Generator:
        def generate(self,q,s,h):
            assert any(v.id=='faq-14:0' for v in s)
            return Generation(outcome='answered',message='The replacement fee is ₹200.',source_ids=['faq-14:0'])
    app.dependency_overrides[get_generator]=lambda:Generator()
    first=client.post('/api/chat',json={'message':'How do I replace my ID?'}).json()
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    followup=client.post('/api/chat',json={'message':'so how much do i pay?','conversation_id':first['conversation_id']}).json()
    assert followup['outcome']=='answered' and '200' in followup['message']
    with Session(database) as db:
        db.get(Document,'faq-14').approved=False;db.commit()
    revoked=client.post('/api/chat',json={'message':'and how much was that again?','conversation_id':first['conversation_id']}).json()
    assert revoked['outcome']=='needs_staff_confirmation'

def test_ticket_targets_confirmed_message_not_latest(grounded,database):
    one=grounded.post('/api/chat',json={'message':'First question'}).json()
    two=grounded.post('/api/chat',json={'message':'Different question','conversation_id':one['conversation_id']}).json()
    url='/api/conversations/'+one['conversation_id']+'/escalate'
    r=grounded.post(url,json={'message_id':one['user_message_id'],'confirmed':True})
    assert r.status_code==200
    with Session(database) as db:
        assert db.scalar(select(Ticket)).query=='First question'
    foreign=grounded.post('/api/chat',json={'message':'Separate conversation'}).json()
    assert grounded.post(url,json={'message_id':foreign['user_message_id'],'confirmed':True}).status_code==404

def test_model_unsupported_also_waits_for_confirmation(grounded,database):
    class Generator:
        def generate(self,*args):return Generation(outcome='unsupported',message='No supporting fact.',source_ids=[])
    app.dependency_overrides[get_generator]=lambda:Generator()
    result=grounded.post('/api/chat',json={'message':'Unknown detail?'}).json()
    assert result['outcome']=='needs_staff_confirmation' and not result['ticket_reference']
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()

def test_query_resolution_failure_is_retryable_and_does_not_create_tickets(grounded,database):
    first=grounded.post('/api/chat',json={'message':'How do I replace an ID?'}).json()
    class UnavailableResolver:
        def resolve(self,*args):raise HTTPException(502,'The answer service could not complete this request. Please try again.')
    app.dependency_overrides[get_query_resolver]=lambda:UnavailableResolver()
    result=grounded.post('/api/chat',json={'message':'so how much do i pay?','conversation_id':first['conversation_id']})
    assert result.status_code==502
    with Session(database) as db:
        assert not db.scalars(select(Ticket)).all()
        assert len(db.scalars(select(Message)).all())==2

def test_query_rewriter_receives_conversation_and_returns_search_question(monkeypatch):
    import httpx
    monkeypatch.setattr(settings(),'openrouter_api_key','fixture-key')
    monkeypatch.setattr(settings(),'openrouter_model','fixture-model')
    def respond(self,url,**kwargs):
        messages=kwargs['json']['messages']
        assert messages[1]=={'role':'user','content':'How do I replace a lost ID?'}
        assert messages[2]['role']=='assistant' and '200' in messages[2]['content']
        assert 'so how much do i pay?' in messages[-1]['content']
        return httpx.Response(200,request=httpx.Request('POST',url),json={'choices':[{'message':{'content':'{"query":"What is the lost ID replacement fee?","uses_context":true}'}}]})
    monkeypatch.setattr(httpx.Client,'post',respond)
    result=OpenRouterGenerator().resolve('so how much do i pay?',[{'role':'user','content':'How do I replace a lost ID?'},{'role':'assistant','content':'Use the portal. The fee is ₹200.'}])
    assert result.uses_context and result.query=='What is the lost ID replacement fee?'

def test_maximum_length_question_and_strict_ticket_confirmation(client):
    app.dependency_overrides[get_retriever]=lambda:lambda db,q:[]
    result=client.post('/api/chat',json={'message':'x'*2000})
    assert result.status_code==200
    reply=result.json()
    for invalid in [1,'true',False,None]:
        response=client.post('/api/conversations/'+reply['conversation_id']+'/escalate',json={'message_id':reply['user_message_id'],'confirmed':invalid})
        assert response.status_code==422


def test_citation_repair_saves_only_valid_answer(grounded,database,source,monkeypatch):
    generator=OpenRouterGenerator()
    attempts=[]
    def request(*args):
        attempts.append(args)
        return Generation(outcome='answered',message=source.content,source_ids=[source.document_id if len(attempts)==1 else source.id])
    monkeypatch.setattr(generator,'_request',request)
    app.dependency_overrides[get_generator]=lambda:generator
    r=grounded.post('/api/chat',json={'message':'What are the robotics lab hours?'})
    assert r.status_code==200 and len(attempts)==2
    assert r.json()['sources'][0]['id']==source.id
    assert r.json()['ticket_reference'] is None
    with Session(database) as db:
        assert len(db.scalars(select(Message)).all())==2
        assert not db.scalars(select(Ticket)).all()


def test_failed_citation_repair_saves_no_answer_or_ticket(grounded,database,monkeypatch):
    generator=OpenRouterGenerator()
    attempts=[]
    def request(*args):
        attempts.append(args)
        return Generation(outcome='answered',message='Unvalidated answer.',source_ids=['invented'])
    monkeypatch.setattr(generator,'_request',request)
    app.dependency_overrides[get_generator]=lambda:generator
    assert grounded.post('/api/chat',json={'message':'Robotics lab hours?'}).status_code==502
    assert len(attempts)==2
    with Session(database) as db:
        assert not db.scalars(select(Message)).all()
        assert not db.scalars(select(Conversation)).all()
        assert not db.scalars(select(Ticket)).all()
