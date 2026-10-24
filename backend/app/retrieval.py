from functools import lru_cache
import re
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from .models import Document, Chunk
from .schemas import Source
from .config import settings

STOP = set('a an the is are was where when what how do does can i my to in on of for me it and please tell about which'.split())

def tokens(text):
    return set(re.findall(r'[a-z0-9]+', text.lower())) - STOP

@lru_cache
def embedding_model():
    # Lazy load: importing the API never downloads a model.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings().embedding_model)

def embed(texts: list[str]) -> list[list[float]]:
    return embedding_model().encode(texts, normalize_embeddings=True).tolist()

def cosine(a, b):
    import math
    return sum(x*y for x,y in zip(a,b)) / max(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)), 1e-9)

def retrieve(db: Session, query: str, encode=embed):
    vector = encode([query])[0]
    stmt = select(Chunk, Document).join(Document).where(Document.approved.is_(True))
    words = tokens(query)
    if db.bind.dialect.name == 'postgresql':
        semantic = db.execute(stmt.order_by(Chunk.embedding.cosine_distance(vector)).limit(12)).all()
        terms=[w for w in sorted(words) if len(w)>=3][:32]
        lexical = db.execute(stmt.where(or_(*[Chunk.content.ilike(f'%{w}%') for w in terms])).limit(30)).all() if terms else []
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
    return [s for _,s in scored[:8]]
