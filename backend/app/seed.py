"""Run after migrations: uv run python -m app.seed. Re-running updates seed records."""
import json
import re
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy.orm import Session
from .db import engine
from .models import Document, Chunk
from .retrieval import embed
ROOT=Path(__file__).resolve().parents[2] / 'knowledge'

def sample_documents():
    faqs=json.loads((ROOT/'faqs.json').read_text())
    documents=[]
    for item in json.loads((ROOT/'documents.json').read_text()):
        content=(ROOT/item['file']).read_text()
        documents.append(dict(id=item['id'],title=item['title'],category=item['category'],kind='document',content=content,approved=True))
    return faqs+documents

def sections(doc):
    if doc['kind']=='faq':
        return [(doc['title'],doc.get('question','')+'\n'+doc['content'])]
    result=[]
    for part in re.split(r'^## ',doc['content'],flags=re.M)[1:]:
        heading,_,body=part.partition('\n')
        result.append((heading.strip(),body.strip()))
    return result or [(doc['title'],doc['content'])]

def seed(db,encode=embed):
    docs=sample_documents()
    passages=[(d,i,h,c) for d in docs for i,(h,c) in enumerate(sections(d))]
    embeddings=encode([d['title']+'\n'+h+'\n'+c for d,i,h,c in passages])
    for d in docs:
        db.merge(Document(**{k:v for k,v in d.items() if k!='question'}))
    db.flush()
    db.execute(delete(Chunk).where(Chunk.document_id.in_([d['id'] for d in docs])))
    for (d,i,h,c),v in zip(passages,embeddings,strict=True):
        db.add(Chunk(id=f"{d['id']}:{i}",document_id=d['id'],heading=h,content=c,embedding=v))
    db.commit()
    return len(docs),len(passages)

if __name__=='__main__':
    with Session(engine()) as db:
        count,chunks=seed(db)
        print(f'Seeded {count} approved sample sources and {chunks} searchable passages.')
