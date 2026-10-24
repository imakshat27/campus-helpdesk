"""Controlled API evaluation: verifies routing/citations, not live LLM quality."""
import json
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
from app.main import app,get_retriever
from app.llm import get_generator
from app.models import Document
from app.schemas import Source,Generation
ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'knowledge/evaluation.json').read_text())
RESULTS=[]

@pytest.mark.parametrize('case',CASES,ids=[c['query'] for c in CASES])
def test_evaluation(case,client,database,source):
    if case['source']:
        with Session(database) as db:
            d=db.get(Document,case['source'])
            sources=[Source(id=d.id+':0',document_id=d.id,title=d.title,heading=d.title,content=d.content)]
    else:
        sources=[source] if case['expected']=='clarification' else []
    app.dependency_overrides[get_retriever]=lambda: lambda db,q:sources
    class ControlledGenerator:
        def generate(self,q,s,h):
            if case['expected']=='clarification':
                return Generation(outcome='clarification',message='Which lab do you mean?' if 'lab' in q else 'Which event do you mean?',source_ids=[])
            return Generation(outcome='answered',message=s[0].content,source_ids=[s[0].id])
    app.dependency_overrides[get_generator]=lambda:ControlledGenerator()
    result=client.post('/api/chat',json={'message':case['query']})
    assert result.status_code==200
    answer=result.json()
    source_ok=bool(answer['sources']) if case['source'] else not answer['sources']
    content_ok=all(term.lower() in answer['message'].lower() for term in case['contains'])
    ticket_ok=not answer['ticket_reference']
    if case['expected']=='needs_staff_confirmation':
        assert answer['ticket_offer']
        confirmed=client.post('/api/conversations/'+answer['conversation_id']+'/escalate',json={'message_id':answer['user_message_id'],'confirmed':True})
        ticket_ok=confirmed.status_code==200 and bool(confirmed.json()['ticket_reference'])
    passed=answer['outcome']==case['expected'] and source_ok and content_ok and ticket_ok
    RESULTS.append({'query':case['query'],'expected':case['expected'],'actual':answer['outcome'],'answer':answer['message'],'sources':', '.join(s['title'] for s in answer['sources']) or '—','correctness':'PASS (controlled response)' if content_ok and source_ok else 'FAIL','fallback':'Offered first; saved after explicit test confirmation' if case['expected']=='needs_staff_confirmation' else 'Clarification, no ticket' if answer['outcome']=='clarification' else 'Not needed','pass':passed})
    assert passed

@pytest.fixture(scope='module',autouse=True)
def report():
    yield
    if not RESULTS:return
    (ROOT/'reports/controlled-evaluation.json').write_text(json.dumps(RESULTS,indent=2))
    header='# Controlled API evaluation\n\nThis table records real API responses using an isolated SQLite test database and controlled retrieval/generation fixtures. It verifies response handling, citations, clarification, and persisted handoffs. It does **not** measure OpenRouter answer quality, neural retrieval, or Neon/pgvector connectivity. Run the live evaluator for those checks.\n\n'
    lines=['| Query | Expected | Actual | Answer | Source | Correctness | Fallback | Result |','|---|---|---|---|---|---|---|---|']
    for r in RESULTS:
        values=[r['query'],r['expected'],r['actual'],r['answer'],r['sources'],r['correctness'],r['fallback'],'PASS' if r['pass'] else 'FAIL']
        lines.append('| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in values)+' |')
    (ROOT/'reports/controlled-evaluation.md').write_text(header+'\n'.join(lines)+'\n')
