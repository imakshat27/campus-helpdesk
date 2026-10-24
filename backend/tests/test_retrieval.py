from sqlalchemy.orm import Session
from app.models import Chunk,Document
from app.retrieval import retrieve
from app.seed import seed

def vector(index):
    v=[0.0]*384;v[index]=1.0;return v

def test_semantic_candidates_and_approval(database):
    with Session(database) as db:
        db.add(Chunk(id='near',document_id='faq-05',heading='Robot access',content='Weekday supervised project sessions',embedding=vector(0)))
        db.add(Chunk(id='far',document_id='faq-06',heading='Other',content='Different topic',embedding=vector(1)))
        db.commit()
        result=retrieve(db,'robotics access',encode=lambda texts:[vector(0)])
        assert result[0].id=='near'
        assert all(s.id!='far' for s in result)
        db.get(Document,'faq-05').approved=False;db.commit()
        assert retrieve(db,'robotics access',encode=lambda texts:[vector(0)])==[]

def test_seed_is_idempotent_and_sections_have_source_titles(database):
    from sqlalchemy import select,func
    with Session(database) as db:
        for _ in range(2):
            documents,chunks=seed(db,encode=lambda texts:[vector(0) for _ in texts],mode='sample')
        assert documents==29 and chunks>29
        assert db.scalar(select(func.count()).select_from(Document))==29
        assert db.scalar(select(func.count()).select_from(Chunk))==chunks
        assert db.get(Chunk,'event-registration:0').heading=='Campus Hackathon 2026'


def test_retrieval_preserves_provenance_and_diversifies_duplicate_chunks(database):
    from sqlalchemy.orm import Session
    from app.models import Document,Chunk
    with Session(database) as db:
        db.get(Document,'faq-05').source_url='https://vit.ac.in/academics/library'
        db.get(Document,'faq-05').campus='Vellore'
        for i in range(6):
            db.add(Chunk(id=f'duplicate-{i}',document_id='faq-05',heading='Borrowing',content='Library borrowing rules for students',embedding=vector(0)))
        db.add(Chunk(id='other-document',document_id='faq-06',heading='Other access',content='Library borrowing access details',embedding=vector(0)))
        db.commit()
        rows=retrieve(db,'library borrowing',encode=lambda texts:[vector(0)])
        assert len([r for r in rows if r.document_id=='faq-05'])==1
        assert any(r.id=='other-document' for r in rows)
        official=next(r for r in rows if r.document_id=='faq-05')
        assert official.source_url=='https://vit.ac.in/academics/library' and official.campus=='Vellore'
