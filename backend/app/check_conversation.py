"""Live context and consent regression, run with python -m app.check_conversation."""
import json
from pathlib import Path
import httpx
from .config import settings
ROOT=Path(__file__).resolve().parents[2]

def run():
    if settings().knowledge_mode=='official':
        from .check_conversation_official import run as official_run
        return official_run()
    rows=[]
    s=settings()
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=100) as c:
        def ask(query,cid=None):
            r=c.post('/api/chat',json={'message':query,'conversation_id':cid});r.raise_for_status()
            a=r.json();rows.append({'query':query,'outcome':a['outcome'],'answer':a['message'],'sources':[v['title'] for v in a['sources']],'ticket':a['ticket_reference']})
            return a
        first=ask('How do I replace a lost student ID?')
        fee=ask('so how much do i pay?',first['conversation_id'])
        assert fee['outcome']=='answered' and '200' in fee['message'],fee
        collection=ask('And where do I collect it once it is ready?',first['conversation_id'])
        assert collection['outcome']=='answered' and 'support' in collection['message'].lower(),collection
        timing=ask('How long do I have to wait before I can collect it?',first['conversation_id'])
        assert timing['outcome']=='answered' and ('three' in timing['message'].lower() or '3' in timing['message']),timing
        change=ask('What time does the library close on Sunday?',first['conversation_id'])
        assert change['outcome']=='answered' and '5:00' in change['message'],change
        auth=(s.staff_username,s.staff_password)
        def queue():
            r=c.get('/api/staff/tickets?status=all',auth=auth);r.raise_for_status();return r.json()
        count_before=len(queue())
        missing=ask('What is my personal bank account balance?')
        assert missing['outcome']=='needs_staff_confirmation' and not missing['ticket_reference']
        assert len(queue())==count_before,'A ticket was created without consent'
        decline=ask('no thanks',missing['conversation_id'])
        assert decline['outcome']=='conversation' and len(queue())==count_before
        another=ask('Can you tell me tomorrow’s weather in Chennai?')
        assert another['outcome']=='needs_staff_confirmation' and len(queue())==count_before
        yes=ask('yes please',another['conversation_id'])
        assert yes['outcome']=='escalated' and yes['ticket_reference']
        assert len(queue())==count_before+1
        stored=next(v for v in queue() if v['reference']==yes['ticket_reference'])
        assert stored['query']=='Can you tell me tomorrow’s weather in Chennai?'
    (ROOT/'reports/context-and-consent.json').write_text(json.dumps(rows,indent=2))
    lines=['# Live conversation and ticket-consent regression','','All checks passed against the configured OpenRouter model and Neon database. Covers the reported six-word fee follow-up, two further contextual questions, a new topic, a missing answer, decline, and explicit ticket consent. Staff queue counts were checked before and after consent. One test ticket is created only after “yes please”.','','| Query | Outcome | Answer | Sources |','|---|---|---|---|']
    for row in rows:
        lines.append('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in [row['query'],row['outcome'],row['answer'],', '.join(row['sources']) or '—'])+' |')
    (ROOT/'reports/context-and-consent.md').write_text('\n'.join(lines)+'\n')
    print(f'{len(rows)} live turns passed; context preserved, no tickets before consent, exactly one confirmed ticket saved.')
if __name__=='__main__':run()
