from functools import lru_cache
import re
from sqlalchemy import select, or_, case
from sqlalchemy.orm import Session,load_only
from .models import Document, Chunk
from .schemas import Source
from .config import settings

STOP = set('a an the is are was where when what how do does can i my to in on of for me it and please tell about which'.split())

def tokens(text):
    words=set(re.findall(r'[a-z0-9]+', text.lower())) - STOP
    return {w[:-1] if len(w)>4 and w.endswith('s') and not w.endswith('ss') else w for w in words}

@lru_cache
def embedding_model():
    # Lazy load: importing the API never downloads a model.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings().embedding_model,device='cpu')

def embed(texts: list[str]) -> list[list[float]]:
    return embedding_model().encode(texts, normalize_embeddings=True).tolist()

def cosine(a, b):
    import math
    return sum(x*y for x,y in zip(a,b)) / max(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)), 1e-9)

def retrieve(db: Session, query: str, encode=embed):
    expanded=query
    for phrase,related in {'day scholar':'hostel residence residential day scholars','id card':'identity card duplicate replacement student records','bonafide':'bonafide certificate student records','revaluation':'revaluation rechecking examination marks'}.items():
        if phrase in query.casefold():expanded+=' '+related
    vector = encode([expanded])[0]
    stmt = select(Chunk, Document).options(load_only(Document.id,Document.title,Document.source_url,Document.campus,Document.retrieved_at)).join(Document).where(Document.approved.is_(True))
    words = tokens(query)
    if db.bind.dialect.name == 'postgresql':
        semantic = db.execute(stmt.order_by(Chunk.embedding.cosine_distance(vector)).limit(12)).all()
        terms=[w for w in sorted(words) if len(w)>=3][:32]
        lexical_rank=sum(case((Chunk.content.ilike(f'%{w}%'),1),else_=0) for w in terms)
        lexical = db.execute(stmt.where(or_(*[Chunk.content.ilike(f'%{w}%') for w in terms])).order_by(lexical_rank.desc()).limit(30)).all() if terms else []
        candidates = {c.id:(c,d) for c,d in [*semantic,*lexical]}.values()
    else:
        # Only used by the isolated test database. Production uses pgvector above.
        candidates = db.execute(stmt).all()
    scored=[]
    for c,d in candidates:
        semantic = cosine(vector,c.embedding)
        lexical = len(words & tokens(f'{d.title} {c.heading} {c.content}')) / max(len(words),1)
        score = 0.8*semantic + 0.2*lexical
        if semantic >= settings().retrieval_threshold or (len(words)>=2 and lexical>=0.8):
            scored.append((score, Source(id=c.id,document_id=d.id,title=d.title,heading=c.heading,content=c.content,source_url=d.source_url,campus=d.campus,retrieved_at=d.retrieved_at)))
    scored.sort(key=lambda item:item[0], reverse=True)
    # Avoid spending the entire answer context on duplicate/mobile copies or
    # adjacent chunks from one long document. Keep multiple source families.
    result=[];seen=set();per_document={}
    for _,source in scored:
        signature=' '.join(source.content.casefold().split())
        if signature in seen or per_document.get(source.document_id,0)>=3:continue
        result.append(source);seen.add(signature)
        per_document[source.document_id]=per_document.get(source.document_id,0)+1
        if len(result)==8:break
    return result
