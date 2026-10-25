"""Isolated browser acceptance server; never contacts Neon or the model.

BROWSER_TEST_CREDENTIALS names a private temporary JSON file and
BROWSER_TEST_DATABASE names an isolated SQLite file, both outside the repository.
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app,get_retriever
from app.db import get_db
from app.events import get_event_engine
from app.config import settings
from app.models import Base,Document
from app.provision_accounts import provision
from app.llm import get_generator,get_query_resolver,ResolvedQuery
from app.schemas import Generation,Source

credentials=json.loads(Path(os.environ['BROWSER_TEST_CREDENTIALS']).read_text())
bind=create_engine('sqlite:///'+os.environ['BROWSER_TEST_DATABASE'],connect_args={'check_same_thread':False,'timeout':30})
Base.metadata.create_all(bind)
config=settings();config.cookie_secure=False
config.cors_origins=['http://127.0.0.1:5173','http://localhost:5173']
config.chat_requests_per_minute=config.chat_requests_per_day=1000
config.session_requests_per_minute=config.session_requests_per_day=1000
with Session(bind) as db:
    provision(db,SimpleNamespace(**credentials))
    if not db.get(Document,'browser-source'):
        db.add(Document(id='browser-source',title='Controlled browser test source',category='library',kind='faq',content='Controlled test: library books can be renewed at the desk.'))
        db.commit()

def database():
    with Session(bind) as db:yield db
source=Source(id='browser-source:0',document_id='browser-source',title='Controlled browser test source',heading='Renewals',content='Controlled test: library books can be renewed at the desk.')
class Generator:
    def generate(self,query,sources,history):
        return Generation(outcome='answered',message=sources[0].content,source_ids=[source.id])
class Resolver:
    def resolve(self,query,history):return ResolvedQuery(query=query,uses_context=False)
app.dependency_overrides[get_db]=database
app.dependency_overrides[get_event_engine]=lambda:bind
app.dependency_overrides[get_retriever]=lambda:lambda db,q:[] if 'private' in q.lower() else [source]
app.dependency_overrides[get_generator]=lambda:Generator()
app.dependency_overrides[get_query_resolver]=lambda:Resolver()
