"""Repair provider citations once while always enforcing the retrieved allowlist."""
import pytest
from fastapi import HTTPException
from app.llm import OpenRouterGenerator, validate_generation
from app.schemas import Generation, Source

@pytest.fixture
def evidence():
    return [Source(id='faq-14:0',document_id='faq-14',title='Replacing a lost student ID',heading='Replacement fee',content='The sample replacement fee is ₹200.')]

@pytest.mark.parametrize('bad_ids',[['faq-14'],['Replacing a lost student ID'],['invented'],[]])
def test_repairs_bad_citations_using_same_evidence(monkeypatch,evidence,bad_ids):
    calls=[]
    history=[{'role':'user','content':'I lost my ID card.'}]
    def request(system,previous,payload,*args):
        calls.append((system,previous,payload))
        return Generation(outcome='answered',message='The sample replacement fee is ₹200.',source_ids=bad_ids if len(calls)==1 else ['faq-14:0'])
    generator=OpenRouterGenerator()
    monkeypatch.setattr(generator,'_request',request)
    answer=generator.generate('how much for a new id card?',evidence,history)
    assert answer.source_ids==['faq-14:0'] and '200' in answer.message
    assert len(calls)==2
    assert all(c[1]==history and c[2]['question']=='how much for a new id card?' for c in calls)
    assert calls[0][2]['approved_sources']==[evidence[0].model_dump(exclude={'document_id'})]
    assert calls[1][2]['approved_sources']==calls[0][2]['approved_sources']
    assert calls[1][2]['allowed_source_ids']==['faq-14:0']


def test_repair_is_bounded_and_invalid_answer_still_rejected(monkeypatch,evidence):
    calls=[]
    generator=OpenRouterGenerator()
    def request(*args):
        calls.append(args)
        return Generation(outcome='answered',message='Unsupported answer.',source_ids=['invented'])
    monkeypatch.setattr(generator,'_request',request)
    with pytest.raises(HTTPException) as error:
        generator.generate('ID fee?',evidence,[])
    assert error.value.status_code==502 and len(calls)==2

@pytest.mark.parametrize('outcome,ids',[('answered',['faq-14:0']),('clarification',[]),('unsupported',[])])
def test_valid_response_does_not_retry(monkeypatch,evidence,outcome,ids):
    calls=[]
    generator=OpenRouterGenerator()
    def request(*args):
        calls.append(args)
        return Generation(outcome=outcome,message='A valid response.',source_ids=ids)
    monkeypatch.setattr(generator,'_request',request)
    assert generator.generate('ID fee?',evidence,[]).outcome==outcome
    assert len(calls)==1


def test_transport_failure_is_not_a_citation_retry(monkeypatch,evidence):
    calls=[]
    generator=OpenRouterGenerator()
    def request(*args):
        calls.append(args)
        raise HTTPException(502,'Provider unavailable.')
    monkeypatch.setattr(generator,'_request',request)
    with pytest.raises(HTTPException):
        generator.generate('ID fee?',evidence,[])
    assert len(calls)==1


def test_document_id_never_passes_as_a_passage_id(evidence):
    with pytest.raises(HTTPException):
        validate_generation(Generation(outcome='answered',message='₹200',source_ids=['faq-14']),evidence)

@pytest.mark.parametrize('failure',['json','503','timeout'])
def test_provider_recovers_once_from_transient_or_invalid_output(monkeypatch,failure):
    import httpx
    from app.config import settings
    calls=[]
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,**kwargs):
            calls.append(kwargs)
            request=httpx.Request('POST',url)
            if len(calls)==1:
                if failure=='timeout':raise httpx.ReadTimeout('test timeout')
                if failure=='503':return httpx.Response(503,request=request)
                return httpx.Response(200,request=request,json={'choices':[{'message':{'content':'not valid JSON'}}]})
            return httpx.Response(200,request=request,json={'choices':[{'message':{'content':'{"outcome":"unsupported","message":"No published fact.","source_ids":[]}'}}]})
    monkeypatch.setattr(settings(),'openrouter_api_key','test-key')
    monkeypatch.setattr(settings(),'openrouter_model','test-model')
    monkeypatch.setattr('app.llm.httpx.Client',Client)
    result=OpenRouterGenerator()._request('rules',[],{'question':'test'},Generation,100)
    assert result.outcome=='unsupported' and len(calls)==2

@pytest.mark.parametrize('status,attempts',[(401,1),(429,2),(503,2)])
def test_provider_retry_bound_and_auth_failures(monkeypatch,status,attempts):
    import httpx
    from app.config import settings
    calls=[]
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,**kwargs):
            calls.append(kwargs);return httpx.Response(status,request=httpx.Request('POST',url))
    monkeypatch.setattr(settings(),'openrouter_api_key','test-key')
    monkeypatch.setattr(settings(),'openrouter_model','test-model')
    monkeypatch.setattr('app.llm.httpx.Client',Client)
    with pytest.raises(HTTPException) as error:
        OpenRouterGenerator()._request('rules',[],{'question':'test'},Generation,100)
    assert error.value.status_code==502 and len(calls)==attempts
