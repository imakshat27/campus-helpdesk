"""Real embedding evaluation, isolated database; does not call an LLM or Neon."""
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Base
from .seed import seed
from .retrieval import retrieve
ROOT=Path(__file__).resolve().parents[2]

def run():
    engine=create_engine('sqlite://')
    Base.metadata.create_all(engine)
    cases=json.loads((ROOT/'knowledge/evaluation.json').read_text())
    rows=[]
    with Session(engine) as db:
        seed(db)
        for case in cases:
            sources=retrieve(db,case['query'])
            expected=case['source']
            passed=any(s.document_id==expected for s in sources) if expected else bool(sources) if case['expected']=='clarification' else not sources
            rows.append(dict(query=case['query'],expected=expected or case['expected'],retrieved=[s.title for s in sources],pass_=passed))
    report=['# Neural retrieval check','','Real all-MiniLM-L6-v2 embeddings and production ranking logic, using an isolated SQLite database with cosine similarity computed in Python. This checks retrieval recall and abstention only; it does not exercise the Neon pgvector SQL operator or OpenRouter generation.','','| Query | Expected source / behaviour | Retrieved sources | Result |','|---|---|---|---|']
    for r in rows:
        report.append('| '+' | '.join([r['query'],r['expected'],'; '.join(r['retrieved']) or 'None','PASS' if r['pass_'] else 'REVIEW'])+' |')
    (ROOT/'reports/retrieval-check.md').write_text('\n'.join(report)+'\n')
    print(f"{sum(r['pass_'] for r in rows)}/{len(rows)} retrieval cases passed. See reports/retrieval-check.md.")
    return 0 if all(r['pass_'] for r in rows) else 1
if __name__=='__main__':
    raise SystemExit(run())
