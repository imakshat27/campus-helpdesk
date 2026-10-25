import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app, get_retriever
from app.db import get_db
from app.llm import get_generator, get_query_resolver, ResolvedQuery
from app.events import get_event_engine
from app.models import Base, Document, User, LoginSession, now
from app.access import hasher, digest
from datetime import timedelta
from app.schemas import Generation, Source
from app.seed import sample_documents
from app.config import settings
from app.access import require_access,allow_chat

@pytest.fixture
def database():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for d in sample_documents():
            db.add(Document(**{k:v for k,v in d.items() if k!='question'}))
        db.add(User(id='test-staff', username='test-staff', role='staff', password_hash=hasher.hash('test-staff-password-long')))
        db.add(User(id='test-owner', username='test-student', role='student', password_hash=hasher.hash('test-student-password-long')))
        db.flush()
        db.add(LoginSession(token_hash=digest('test-student-token'), user_id='test-owner', expires_at=now()+timedelta(hours=8)))
        db.add(LoginSession(token_hash=digest('test-staff-token'), user_id='test-staff', expires_at=now()+timedelta(hours=8)))
        db.commit()
    yield engine
    engine.dispose()

@pytest.fixture
def client(database,monkeypatch):
    monkeypatch.setattr(settings(),'staff_username','test-staff')
    monkeypatch.setattr(settings(),'staff_password','test-staff-password-long')
    monkeypatch.setattr(settings(),'cookie_secure',False)
    def db_override():
        with Session(database) as db:
            yield db
    app.dependency_overrides[get_db]=db_override
    app.dependency_overrides[get_event_engine]=lambda:database
    app.dependency_overrides[require_access]=lambda:'test-owner'
    app.dependency_overrides[allow_chat]=lambda:'test-owner'
    class Resolver:
        def resolve(self,query,history):
            context=' '.join(m['content'] for m in history if m['role']=='user')
            return ResolvedQuery(query=(context+' '+query).strip(),uses_context=bool(history))
    app.dependency_overrides[get_query_resolver]=lambda:Resolver()
    with TestClient(app,raise_server_exceptions=False,headers={'Origin':'http://localhost:5173','Cookie':'campus_session=test-student-token'}) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def source(database):
    with Session(database) as db:
        doc=db.get(Document,'faq-05')
        return Source(id='faq-05:0',document_id=doc.id,title=doc.title,heading=doc.title,content=doc.content)

@pytest.fixture
def grounded(client,source):
    app.dependency_overrides[get_retriever]=lambda: lambda db,q:[source]
    class Generator:
        def generate(self,q,s,h):
            return Generation(outcome='answered',message=s[0].content,source_ids=[s[0].id])
    app.dependency_overrides[get_generator]=lambda: Generator()
    return client
