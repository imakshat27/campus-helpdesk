"""Live official-corpus answer evaluation; creates conversations, never confirms tickets."""
import json
from pathlib import Path
import httpx
from .review_client import authenticate
from .config import settings
CASES=[
('What choices does FFCS give students?','answered','ffcs'),
('Who is allowed to register as a day scholar at VIT Vellore?','answered','hostel'),
('Can I borrow library books using another student’s ID card?','answered','library'),
('What does the counselling division offer students?','answered','well-being'),
('What is SASDAL and what support does it provide?','answered','sasdal'),
('How do I apply for an academic transcript?','answered','transcript'),
('Which office handles duplicate student ID cards and bonafide certificates?','answered','administrative'),
('Where can I find the VIT anti-ragging committee information?','answered','ragging'),
('When does the lab open?','clarification',None),
('How much is the hostel fee?','clarification',None),
('What is my personal attendance percentage today?','needs_staff_confirmation',None),
('What is my personal bank account balance?','needs_staff_confirmation',None),
]
def run():
 rows=[];s=settings()
 with httpx.Client(base_url='http://127.0.0.1:8000',timeout=150) as client:
  authenticate(client)
  def count():
   r=client.get('/api/staff/tickets?status=all',auth=(s.staff_username,s.staff_password));r.raise_for_status();return len(r.json())
  before=count()
  for query,outcome,family in CASES:
   r=client.post('/api/chat',json={'message':query});body=r.json();sources=body.get('sources',[])
   correct_family=family is None or any(family in (x.get('source_url') or '').lower() for x in sources)
   passed=r.status_code==200 and body.get('outcome')==outcome and correct_family and not body.get('ticket_reference')
   rows.append({'query':query,'http_status':r.status_code,'expected_outcome':outcome,'actual_outcome':body.get('outcome'),'actual_answer':body.get('message') or body.get('detail'),'expected_source_family':family,'source_family_correct':correct_family,'sources':[{'id':x['id'],'title':x['title'],'url':x.get('source_url')} for x in sources],'ticket_created':bool(body.get('ticket_reference')),'pass':passed})
   print(query,body.get('outcome'),passed,flush=True)
  after=count()
 root=Path(__file__).resolve().parents[2]/'reports'
 result={'checks':'Automatic outcome/source-family checks; not independent factual correctness review','tickets_before':before,'tickets_after':after,'rows':rows}
 (root/'official-live-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 lines=['# Live official Vellore evaluation','','Actual OpenRouter/Neon answers. Automatic checks cover outcome, source family and absence of saved tickets; they do not independently verify every factual claim. Read the answers against their original sources for critical decisions. No ticket was confirmed by this evaluator.','','| Query | Actual answer | Outcome | Source family | Ticket created | Check |','|---|---|---|---|---|---|']
 for row in rows:lines.append('| '+' | '.join(str(x).replace('\n',' ').replace('|','/') for x in [row['query'],row['actual_answer'],row['actual_outcome'],row['source_family_correct'],row['ticket_created'],'PASS' if row['pass'] else 'FAIL'])+' |')
 lines+=['',f'Ticket count before/after: {before}/{after}.']
 (root/'official-live-evaluation.md').write_text('\n'.join(lines)+'\n')
 print('Passed',sum(r['pass'] for r in rows),'of',len(rows),'tickets unchanged',before==after)
if __name__=='__main__':run()
