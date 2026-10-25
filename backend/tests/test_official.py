import json
import re
from app.import_official import extract_html,vellore_only,ROOT
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


def test_vellore_filter_drops_other_campus_lines_sections_and_table_cells():
 text='## Sports in Chennai campus\n\nTennis court\n\n## Sports at Vellore\n\nCricket\n\n* VIT-Vellore only IFT.\n* VIT-AP only IFT.\n\n| a | b |\n| --- | --- |\n| VIT Vellore Campus | VIT Bhopal Campus |\n| VIT Chennai | Amaravati |'
 result=vellore_only(text)
 assert 'Tennis' not in result and 'VIT-AP' not in result and 'Bhopal' not in result and 'Amaravati' not in result
 assert 'Cricket' in result and 'VIT-Vellore only IFT' in result and 'VIT Vellore Campus' in result and '| --- | --- |' in result

def test_imported_corpus_is_vellore_only():
 manifest=json.loads((ROOT/'manifest.json').read_text())
 other=re.compile(r'\\b(chennai|bhopal|amaravati|andhra|vit[\\s-]?ap)\\b',re.I)
 assert manifest['documents'] and all(d['campus']=='Vellore' for d in manifest['documents'])
 assert all(d['source_url'].startswith('https://vit.ac.in/') for d in manifest['documents'])
 assert not [d['title'] for d in manifest['documents'] if other.search((ROOT/d['file']).read_text())]
