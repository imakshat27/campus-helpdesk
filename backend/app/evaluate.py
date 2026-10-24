"""Live evaluation; ticket cases explicitly simulate confirmation as a second step."""
import argparse,csv,json,re
from pathlib import Path
import httpx
from .review_client import authenticate
ROOT=Path(__file__).resolve().parents[2]

def normalized_text(value):
    value=value.casefold()
    months='january|february|march|april|may|june|july|august|september|october|november|december'
    value=re.sub(r'\b('+months+r')\s+(\d{1,2}),?\s+(\d{4})\b',lambda m:f'{m[2]} {m[1]} {m[3]}',value)
    return re.sub(r'\b(\d+)\s*(?:to|[–—-])\s*(\d+)\b',r'\1–\2',value)

def run(base_url):
    rows=[]
    with httpx.Client(base_url=base_url,timeout=100) as client:
        authenticate(client)
        for case in json.loads((ROOT/'knowledge/evaluation.json').read_text()):
            try:
                response=client.post('/api/chat',json={'message':case['query']})
                response.raise_for_status();data=response.json()
                outcome_ok=data['outcome']==case['expected']
                exact_source=any(s['document_id']==case['source'] for s in data['sources']) if case['source'] else not data['sources']
                content_ok=all(normalized_text(term) in normalized_text(data['message']) for term in case['contains'])
                consent_ok=not data.get('ticket_reference')
                reference=''
                fallback='Not needed'
                if case['expected']=='needs_staff_confirmation':
                    consent_ok=consent_ok and bool(data.get('ticket_offer'))
                    # The initial response must not contain a ticket. The evaluator
                    # then explicitly simulates a student's affirmative button click.
                    if consent_ok:
                        confirmed=client.post('/api/conversations/'+data['conversation_id']+'/escalate',json={'message_id':data['user_message_id'],'confirmed':True})
                        confirmed.raise_for_status();reference=confirmed.json()['ticket_reference']
                    consent_ok=consent_ok and bool(reference)
                    fallback='Offered first; ticket saved after explicit test confirmation' if consent_ok else 'FAIL: consent flow'
                elif case['expected']=='clarification':
                    fallback='Clarification; no ticket'
                passed=outcome_ok and consent_ok and content_ok and exact_source
                rows.append(dict(query=case['query'],expected=case['expected'],actual=data['outcome'],answer=data['message'],sources='; '.join(s['title'] for s in data['sources']),correctness='PASS (heuristic; review facts)' if content_ok and exact_source else 'REVIEW',fallback=fallback,ticket_reference=reference,result='PASS' if passed else 'REVIEW'))
            except (httpx.HTTPError,KeyError,ValueError) as exc:
                rows.append(dict(query=case['query'],expected=case['expected'],actual='ERROR',answer=str(exc),sources='',correctness='NOT RUN',fallback='NOT RUN',ticket_reference='',result='ERROR'))
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    (out/'live-evaluation.json').write_text(json.dumps(rows,indent=2))
    with (out/'live-evaluation.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# Live evaluation','', 'Actual API responses using the configured OpenRouter model and Neon. Unsupported questions must offer a ticket without creating one. For those two cases the evaluator then explicitly simulates student confirmation in a separate request. Automated answer checks normalize equivalent date/range formatting but still require source review.','', '| Query | Expected | Actual | Answer | Source | Correctness | Fallback | Result |','|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| '+' | '.join(str(r[k]).replace('|','/').replace('\n',' ') for k in ['query','expected','actual','answer','sources','correctness','fallback','result'])+' |')
    (out/'live-evaluation.md').write_text('\n'.join(lines)+'\n')
    print(f"{sum(r['result']=='PASS' for r in rows)}/{len(rows)} passed automatic checks. Review reports/live-evaluation.md.")
    return 1 if any(r['result']!='PASS' for r in rows) else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    raise SystemExit(run(parser.parse_args().base_url))
