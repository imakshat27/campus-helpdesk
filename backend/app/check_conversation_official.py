"""Live official-corpus context and consent check; confirms one demo ticket."""
import json
from pathlib import Path
import httpx
from .config import settings

def run():
 rows=[];s=settings()
 with httpx.Client(base_url='http://127.0.0.1:8000',timeout=150) as c:
  def ask(q,cid=None):
   response=c.post('/api/chat',json={'message':q,'conversation_id':cid});response.raise_for_status();a=response.json()
   rows.append({'query':q,'outcome':a['outcome'],'answer':a['message'],'sources':[{'id':x['id'],'title':x['title'],'url':x.get('source_url')} for x in a['sources']],'ticket':a['ticket_reference']})
   return a
  first=ask('How do freshers book hostel accommodation at VIT Vellore?')
  assert first['outcome']=='answered' and any('hostel' in (x.get('source_url') or '').lower() for x in first['sources'])
  follow=ask('When can I report there before orientation?',first['conversation_id'])
  assert follow['outcome']=='answered' and 'day' in follow['message'].lower()
  library=ask('What are the VIT library working hours on Sundays?',first['conversation_id'])
  assert library['outcome']=='answered' and any('library' in x['source_url'] for x in library['sources'])
  returned=ask('Back to the hostel booking, how do I pay for my room and mess?',first['conversation_id'])
  assert returned['outcome']=='answered' and any('hostel' in x['source_url'].lower() for x in returned['sources'])
  def queue():
   r=c.get('/api/staff/tickets?status=all',auth=(s.staff_username,s.staff_password));r.raise_for_status();return r.json()
  count=len(queue())
  missing=ask('What is my personal bank balance?')
  assert missing['outcome']=='needs_staff_confirmation' and not missing['ticket_reference'] and len(queue())==count
  declined=ask('No thanks',missing['conversation_id'])
  assert declined['outcome']=='conversation' and len(queue())==count
  other=ask('What is my private VTOP password?')
  assert other['outcome']=='needs_staff_confirmation' and len(queue())==count
  yes=ask('yes please',other['conversation_id'])
  assert yes['outcome']=='escalated' and yes['ticket_reference'] and len(queue())==count+1
 root=Path(__file__).resolve().parents[2]/'reports'
 (root/'official-context-and-consent.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 (root/'official-context-and-consent.md').write_text('# Official corpus: live context and consent\n\nPassed eight live turns, including a hostel follow-up, a library topic switch, explicit return to hostel booking, unsupported questions, decline, and exactly one ticket after explicit confirmation. Uses the configured OpenRouter model and Neon.\n\n| Query | Outcome | Actual answer | Sources |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join([r['query'],r['outcome'],r['answer'].replace('\n',' ').replace('|','/'),'; '.join(x['title'] for x in r['sources']) or '—'])+' |' for r in rows)+'\n')
 print('8 live official context/consent turns passed; exactly one confirmed ticket.')
if __name__=='__main__':run()
