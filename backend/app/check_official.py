"""Real retrieval coverage evaluation against the active official vector corpus."""
import json
from pathlib import Path
from sqlalchemy.orm import Session
from .db import engine
from .retrieval import retrieve
CASES=[
('What are library working hours on Sunday?','library'),
('How many books may an undergraduate borrow from the library?','library'),
('Can I renew a library book online?','library'),
('What happens if I lose a library book?','library'),
('Can I access library electronic journals off campus?','library'),
('What is the attendance requirement for examinations?','academic'),
('What is the grading system and CGPA?','academic'),
('Can I withdraw a registered course?','academic'),
('How does FFCS let me choose courses and faculty?','ffcs'),
('What is the minimum and maximum credit load?','academic'),
('How do freshers book a hostel?','hostel'),
('When can freshers report to the hostel?','hostel'),
('Who can register as a day scholar?','hostel'),
('What is the hostel fee refund policy for 2026-27?','hostel'),
('What mess options are available in the hostel?','hostel'),
('How can I contact the Office of Students Welfare?','studentswelfare'),
('What support is provided by the counselling division?','well-being'),
('What is SASDAL disability support?','sasdal'),
('How do I report ragging?','ragging'),
('What is the student code of conduct?','conduct'),
('Where are sports facilities and the physical education department?','sports'),
('What health services are available on campus?','healthservices'),
('How do I apply for an academic transcript?','transcript'),
('How do alumni contact the alumni office?','alumni'),
('What is the Career Development Centre?','cdc'),
('What scholarships does VIT offer?','scholarship'),
('How do international transfer programmes work?','itp'),
('What research programmes and PhD admissions are available?','research'),
('What are the library rules for visitors?','library'),
('How are hostel room and mess fees paid?','hostel'),
]
def run():
 rows=[]
 with Session(engine()) as db:
  for query,expected in CASES:
   sources=retrieve(db,query)
   rows.append({'query':query,'expected_url_contains':expected,'pass':any(expected in (s.source_url or '').lower() for s in sources),'sources':[{'id':s.id,'title':s.title,'heading':s.heading,'url':s.source_url} for s in sources]})
 root=Path(__file__).resolve().parents[2]/'reports'
 (root/'official-retrieval.json').write_text(json.dumps(rows,indent=2)+'\n')
 lines=['# Official-source retrieval coverage','','Real Sentence Transformers embeddings and Neon pgvector retrieval. A pass means the expected source family appears in the top eight; it does not establish generated-answer correctness.','','| Query | Source family | Retrieved |','|---|---|---|']
 lines+=['| '+r['query']+' | '+r['expected_url_contains']+' | '+('PASS' if r['pass'] else 'FAIL')+' |' for r in rows]
 (root/'official-retrieval.md').write_text('\n'.join(lines)+'\n')
 print(f"Retrieval coverage: {sum(r['pass'] for r in rows)}/{len(rows)}")
 print('Failed queries:',[r['query'] for r in rows if not r['pass']])
if __name__=='__main__':run()
