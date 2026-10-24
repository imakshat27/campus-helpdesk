import secrets
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import Document, Chunk, Conversation, Message, Ticket, now
from .schemas import ChatRequest, ChatResponse, Generation, TicketUpdate, TicketOffer, EscalationRequest, Source
from .retrieval import retrieve
from .llm import get_generator, get_query_resolver, validate_generation
from .clarification import clarification_for
from .conversation import ticket_decision, conversational_reply

app=FastAPI(title='Campus Helpdesk API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=settings().cors_origins,allow_credentials=False,allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'])
security=HTTPBasic(auto_error=False)

@app.exception_handler(SQLAlchemyError)
def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503,content={'detail':'The database is unavailable. Nothing has been confirmed as saved. Please try again.'})

def staff(credentials: HTTPBasicCredentials | None=Depends(security)):
    s=settings()
    if not s.staff_username or not s.staff_password:
        raise HTTPException(503,'Staff access is not configured.')
    if credentials is None:
        raise HTTPException(401,'Sign in to view the staff queue.',headers={'WWW-Authenticate':'Basic'})
    user_ok=secrets.compare_digest(credentials.username.encode(),s.staff_username.encode())
    password_ok=secrets.compare_digest(credentials.password.encode(),s.staff_password.encode())
    if not (user_ok and password_ok):
        raise HTTPException(401,'Incorrect username or password.',headers={'WWW-Authenticate':'Basic'})

def get_retriever():
    return retrieve

@app.get('/api/health')
def health(db: Session=Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'database':'connected','answer_service_configured':bool(settings().openrouter_api_key and settings().openrouter_model),'scenario_date':'2026-10-16','sample_data':True}

@app.get('/api/knowledge')
def knowledge(q: str='',category: str='',db: Session=Depends(get_db)):
    stmt=select(Document).where(Document.approved.is_(True))
    if q.strip():
        stmt=stmt.where(Document.content.ilike('%'+q.strip()+'%') | Document.title.ilike('%'+q.strip()+'%'))
    if category:
        stmt=stmt.where(Document.category==category)
    docs=db.scalars(stmt.order_by(Document.kind,Document.title)).all()
    return [{'id':d.id,'title':d.title,'category':d.category,'kind':d.kind,'content':d.content} for d in docs]

@app.get('/api/knowledge/{document_id}')
def source_detail(document_id: str,db: Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d or not d.approved:
        raise HTTPException(404,'Source not found.')
    return {'id':d.id,'title':d.title,'category':d.category,'kind':d.kind,'content':d.content}

def recent_messages(db, conversation_id):
    rows=db.scalars(select(Message).where(Message.conversation_id==conversation_id).order_by(Message.created_at.desc(),Message.id.desc()).limit(20)).all()
    return list(reversed(rows))

def history_for(db,conversation_id):
    return [{'role':m.role,'content':m.content} for m in recent_messages(db,conversation_id)]

def create_ticket(db, conversation_id, query, reason):
    existing=db.scalar(select(Ticket).where(Ticket.conversation_id==conversation_id,Ticket.query==query,Ticket.status=='open'))
    if existing:
        return existing
    ticket=Ticket(reference='HD-'+uuid4().hex[:10].upper(),conversation_id=conversation_id,query=query,reason=reason)
    db.add(ticket)
    db.flush()
    return ticket

def pending_question(messages):
    if not messages or messages[-1].outcome!='needs_staff_confirmation':
        return None
    return next((m for m in reversed(messages[:-1]) if m.role=='user'),None)

def context_sources(db, messages):
    """Re-read prior citations so withdrawn/edited sources are never trusted from history."""
    previous=next((m for m in reversed(messages) if m.role=='assistant' and m.sources),None)
    if not previous:
        return []
    ids=[s['id'] for s in previous.sources if 'id' in s]
    rows=db.execute(select(Chunk,Document).join(Document).where(Chunk.id.in_(ids),Document.approved.is_(True))).all()
    return [Source(id=c.id,document_id=d.id,title=d.title,heading=c.heading,content=c.content) for c,d in rows]

def save_reply(db,conversation,query,outcome,message,sources=None,reference=None,offer=False):
    user=Message(conversation_id=conversation.id,role='user',content=query,created_at=now())
    db.add(user)
    db.flush()
    db.add(Message(conversation_id=conversation.id,role='assistant',content=message,outcome=outcome,sources=[s.model_dump() for s in (sources or [])],created_at=now()))
    db.commit()
    return ChatResponse(conversation_id=conversation.id,user_message_id=user.id,outcome=outcome,message=message,sources=sources or [],ticket_reference=reference,ticket_offer=TicketOffer(message_id=user.id,query=query) if offer else None)

@app.get('/api/conversations/{conversation_id}')
def conversation_detail(conversation_id: str,db: Session=Depends(get_db)):
    if not db.get(Conversation,conversation_id):
        raise HTTPException(404,'Conversation not found.')
    messages=db.scalars(select(Message).where(Message.conversation_id==conversation_id).order_by(Message.created_at,Message.id)).all()
    return {'conversation_id':conversation_id,'messages':[{'id':m.id,'role':m.role,'content':m.content,'outcome':m.outcome,'sources':m.sources} for m in messages]}

@app.post('/api/chat',response_model=ChatResponse)
def chat(body: ChatRequest,db: Session=Depends(get_db),generator=Depends(get_generator),search=Depends(get_retriever),resolver=Depends(get_query_resolver)):
    query=body.message.strip()
    if not query:
        raise HTTPException(422,'Enter a question first.')
    if body.conversation_id:
        conversation=db.scalar(select(Conversation).where(Conversation.id==str(body.conversation_id)).with_for_update())
        if not conversation:
            raise HTTPException(404,'Conversation not found. Start a new conversation.')
    else:
        conversation=Conversation()
        db.add(conversation)
        db.flush()
    messages=recent_messages(db,conversation.id)
    history=[{'role':m.role,'content':m.content} for m in messages]
    pending=pending_question(messages)
    decision=ticket_decision(query)
    if pending and decision is not None:
        if decision:
            ticket=create_ticket(db,conversation.id,pending.content,'Student confirmed a support ticket')
            return save_reply(db,conversation,query,'escalated','I’ve raised a ticket for your question. Student support can review it in the staff queue.',reference=ticket.reference)
        return save_reply(db,conversation,query,'conversation','Okay, I won’t raise a ticket. You can ask another question whenever you’re ready.')
    greeting=conversational_reply(query)
    if greeting:
        return save_reply(db,conversation,query,'conversation',greeting)
    resolved=resolver.resolve(query,history)
    try:
        sources=search(db,resolved.query)
        if resolved.uses_context:
            # The last grounded answer is often more specific than a fresh vector hit.
            sources=list({s.id:s for s in [*context_sources(db,messages),*sources]}.values())[:8]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503,'Knowledge search is unavailable. Please try again.') from exc
    clarification=clarification_for(query,sources,history)
    if clarification:
        result=Generation(outcome='clarification',message=clarification,source_ids=[])
    elif sources:
        result=validate_generation(generator.generate(query,sources,history),sources)
    else:
        result=Generation(outcome='unsupported',message='I could not find that information in the approved campus knowledge base.',source_ids=[])
    if result.outcome=='unsupported':
        return save_reply(db,conversation,query,'needs_staff_confirmation','I couldn’t find an answer in the approved campus information. Would you like me to raise a ticket for student support?',offer=True)
    selected=[s for s in sources if s.id in result.source_ids]
    return save_reply(db,conversation,query,result.outcome,result.message,selected)

@app.post('/api/conversations/{conversation_id}/escalate')
def escalate(conversation_id: str,body: EscalationRequest,db: Session=Depends(get_db)):
    if not db.scalar(select(Conversation).where(Conversation.id==conversation_id).with_for_update()):
        raise HTTPException(404,'Conversation not found.')
    target=db.get(Message,str(body.message_id))
    if not target or target.conversation_id!=conversation_id or target.role!='user':
        raise HTTPException(404,'The question to send was not found in this conversation.')
    ticket=create_ticket(db,conversation_id,target.content,'Student confirmed a support ticket')
    # Persist consent so the next turn no longer sees an unanswered ticket offer.
    confirmation=f'Ticket {ticket.reference} was raised for: {target.content}'
    if not db.scalar(select(Message.id).where(Message.conversation_id==conversation_id,Message.content==confirmation)):
        db.add(Message(conversation_id=conversation_id,role='user',content='Yes, raise a ticket for: '+target.content,created_at=now()))
        db.flush()
        db.add(Message(conversation_id=conversation_id,role='assistant',content=confirmation,outcome='escalated',created_at=now()))
    db.commit()
    return {'ticket_reference':ticket.reference,'message_id':target.id}

@app.get('/api/staff/tickets',dependencies=[Depends(staff)])
def tickets(status: str=Query('open',pattern='^(open|resolved|all)$'),db: Session=Depends(get_db)):
    stmt=select(Ticket).order_by(Ticket.created_at.desc())
    if status!='all':
        stmt=stmt.where(Ticket.status==status)
    rows=db.scalars(stmt.limit(200)).all()
    return [{'id':t.id,'reference':t.reference,'query':t.query,'reason':t.reason,'status':t.status,'created_at':t.created_at,'messages':history_for(db,t.conversation_id)} for t in rows]

@app.patch('/api/staff/tickets/{ticket_id}',dependencies=[Depends(staff)])
def update_ticket(ticket_id: str,body: TicketUpdate,db: Session=Depends(get_db)):
    ticket=db.get(Ticket,ticket_id)
    if not ticket:
        raise HTTPException(404,'Ticket not found.')
    ticket.status=body.status
    db.commit()
    return {'id':ticket.id,'status':ticket.status}
