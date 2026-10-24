from app.import_official import extract_html
from app.seed import sections
from app.llm import bounded_history

def test_html_keeps_direct_div_text_and_tables_without_navigation():
 title,blocks=extract_html('<title>Library | VIT</title><main><nav>Bad navigation</nav><h2>Borrowing</h2><div>Undergraduate students may borrow books.</div><table><tr><th>Category</th><th>Limit</th></tr><tr><td>UG</td><td>5</td></tr></table></main>')
 text='\n'.join(blocks)
 assert 'Undergraduate students' in text and 'UG' in text and '5' in text
 assert 'Bad navigation' not in text and title=='Library | VIT'

def test_chunks_are_bounded_and_cover_long_pdf_sections():
 doc={'kind':'official','title':'Regulations','content':'## Attendance\n'+('word '*1000)}
 chunks=sections(doc)
 assert len(chunks)>5 and all(len(c.split())<=180 for _,c in chunks)
 assert all(h=='Attendance' for h,_ in chunks)

def test_context_preserves_early_subject_after_long_topic_switch():
 history=[{'role':'user' if i%2==0 else 'assistant','content':f'Turn {i}: '+('library borrowing' if i==0 else 'other topics')} for i in range(72)]
 selected=bounded_history(history)
 assert selected[0]['content'].startswith('Turn 0:') and selected[-1]==history[-1]
 assert len(selected)>20
 assert all(row in history for row in selected)

def test_context_budget_and_order():
 history=[{'role':'user','content':f'{i} '+('x'*1000)} for i in range(80)]
 rows=bounded_history(history,budget=8000)
 assert sum(len(r['content']) for r in rows)<=8000
 assert [int(r['content'].split()[0]) for r in rows]==sorted(int(r['content'].split()[0]) for r in rows)

def test_official_ingestion_deactivates_fictional_sources(database):
    from app.seed import seed
    from app.models import Document,Chunk
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    with Session(database) as db:
        count,chunks=seed(db,encode=lambda texts:[[1.0]+[0.0]*383 for _ in texts],mode='official')
        assert count>=40 and chunks>500
        assert db.get(Document,'faq-14').approved is False
        approved=db.scalars(select(Document).where(Document.approved.is_(True))).all()
        assert all(d.source_url and d.campus=='Vellore' for d in approved)
        assert len(approved)==count
