"""Run after migrations: uv run python -m app.seed. Re-running updates seed records."""
import json
import re
from pathlib import Path
from sqlalchemy import delete, update
from sqlalchemy.orm import Session
from .db import engine
from .models import Document, Chunk
from .retrieval import embed
from .config import settings
ROOT=Path(__file__).resolve().parents[2] / 'knowledge'

def sample_documents():
    faqs=json.loads((ROOT/'faqs.json').read_text())
    documents=[]
    for item in json.loads((ROOT/'documents.json').read_text()):
        content=(ROOT/item['file']).read_text()
        documents.append(dict(id=item['id'],title=item['title'],category=item['category'],kind='document',content=content,approved=True))
    return faqs+documents

def official_documents():
    manifest=ROOT/'official/manifest.json'
    if not manifest.exists():
        raise RuntimeError('Run python -m app.import_official before official ingestion.')
    return [dict(id=d['id'],title=d['title'],category=d['category'],kind='official',
                 content=(ROOT/'official'/d['file']).read_text(),approved=True,
                 source_url=d['source_url'],campus=d['campus'],retrieved_at=d['retrieved_at'])
            for d in json.loads(manifest.read_text())['documents'] if d['content_characters']>=200]

def sections(doc):
    if doc['kind']=='faq':
        return [(doc['title'],doc.get('question','')+'\n'+doc['content'])]
    result=[]
    parts=re.split(r'^## ',doc['content'],flags=re.M)
    for part in parts[1:] or parts:
        heading,_,body=part.partition('\n')
        heading=heading.strip()[:190] or doc['title']
        paragraphs=re.split(r'\n\s*\n',body.strip())
        chunk=''
        for paragraph in paragraphs:
            # Bound embeddings to the encoder's context; repeat heading on each section.
            words=paragraph.split()
            pieces=[' '.join(words[i:i+160]) for i in range(0,len(words),140)]
            for piece in pieces:
                if chunk and len((chunk+' '+piece).split())>180:
                    result.append((heading,chunk));chunk=''
                chunk=(chunk+'\n'+piece).strip()
        if chunk:result.append((heading,chunk))
    return result or [(doc['title'],doc['content'])]

def seed(db,encode=embed,mode=None):
    mode=mode or settings().knowledge_mode
    docs=official_documents() if mode=='official' else sample_documents()
    passages=[(d,i,h,c) for d in docs for i,(h,c) in enumerate(sections(d))]
    embeddings=encode([d['title']+'\n'+h+'\n'+c for d,i,h,c in passages])
    # Deactivate superseded corpus, including fictional fees and room/lab timings.
    db.execute(update(Document).values(approved=False))
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
        print(f'Seeded {count} approved sources and {chunks} searchable passages.')
