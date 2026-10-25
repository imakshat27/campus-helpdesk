from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session,load_only
from .config import settings
from .db import get_db
from .models import Document, Chunk, Conversation, Message, Ticket, User, now
from .schemas import ChatRequest, ChatResponse, Generation, TicketUpdate, TicketOffer, EscalationRequest, Source, ConversationCreate, MessageRequest
from .chat_store import conversation_for, append_message, summary, detail, retry_result, remember
from .retrieval import retrieve
from .llm import get_generator, get_query_resolver, validate_generation
from .clarification import clarification_for,asks_for_price,contains_price
from .conversation import ticket_decision, conversational_reply
from .access import require_access, allow_chat, AccessLogin, login, logout, require_user, staff, public_user, reserve_ai

app=FastAPI(title='Campus Helpdesk API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=settings().cors_origins,allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])
@app.middleware('http')
async def protect_origin(request: Request, call_next):
    if request.method in {'POST', 'PATCH', 'DELETE', 'PUT'}:
        origin = request.headers.get('origin')
        if origin not in settings().cors_origins:
            return JSONResponse(status_code=403, content={'detail': 'Request origin is not allowed.'})
    response = await call_next(request)
    if request.url.path.startswith('/api/auth') or request.url.path.startswith('/api/conversations'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.exception_handler(SQLAlchemyError)
def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503,content={'detail':'The database is unavailable. Nothing has been confirmed as saved. Please try again.'})

def get_retriever():
    return retrieve

@app.post('/api/auth/session')
def access_login(body: AccessLogin,request: Request,response: Response,db: Session=Depends(get_db)):
    return login(body,request,response,db)

@app.get('/api/auth/session')
def access_session(user=Depends(require_user)):
    return public_user(user)

@app.delete('/api/auth/session')
def access_logout(request: Request, response: Response, db: Session=Depends(get_db)):
    return logout(request, response, db)

@app.get('/api/health')
def health(db: Session=Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'database':'connected','answer_service_configured':bool(settings().openrouter_api_key and settings().openrouter_model),'scenario_date':None if settings().knowledge_mode=='official' else '2026-10-16','sample_data':settings().knowledge_mode!='official','knowledge_mode':settings().knowledge_mode,'campus':'Vellore'}

@app.get('/api/knowledge')
def knowledge(q: str='',category: str='',db: Session=Depends(get_db)):
    stmt=select(Document).where(Document.approved.is_(True))
    if q.strip():
        stmt=stmt.where(Document.content.ilike('%'+q.strip()+'%') | Document.title.ilike('%'+q.strip()+'%'))
    if category:
        stmt=stmt.where(Document.category==category)
    docs=db.scalars(stmt.order_by(Document.kind,Document.title)).all()
    return [{'id':d.id,'title':d.title,'category':d.category,'kind':d.kind,'content':d.content,'source_url':d.source_url,'campus':d.campus,'retrieved_at':d.retrieved_at} for d in docs]

@app.get('/api/knowledge/{document_id}')
def source_detail(document_id: str,db: Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d or not d.approved:
        raise HTTPException(404,'Source not found.')
    return {'id':d.id,'title':d.title,'category':d.category,'kind':d.kind,'content':d.content,'source_url':d.source_url,'campus':d.campus,'retrieved_at':d.retrieved_at}

def recent_messages(db, conversation_id):
    rows=db.scalars(select(Message).where(Message.conversation_id==conversation_id).order_by(Message.sequence.desc(),Message.created_at.desc(),Message.id.desc()).limit(80)).all()
    return list(reversed(rows))

def history_for(db,conversation_id):
    return [{'role':m.role,'content':m.content} for m in recent_messages(db,conversation_id)]

def create_ticket(db, conversation_id, query, reason, message_id=None):
    existing=db.scalar(select(Ticket).where(Ticket.conversation_id==conversation_id,Ticket.status=='open'))
    if existing:
        return existing
    ticket=Ticket(reference='HD-'+uuid4().hex[:10].upper(),conversation_id=conversation_id,query=query,reason=reason,message_id=message_id)
    db.add(ticket)
    db.flush()
    db.get(Conversation,conversation_id).state='waiting_for_staff'
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
    rows=db.execute(select(Chunk,Document).options(load_only(Document.id,Document.title,Document.source_url,Document.campus,Document.retrieved_at)).join(Document).where(Chunk.id.in_(ids),Document.approved.is_(True))).all()
    return [Source(id=c.id,document_id=d.id,title=d.title,heading=c.heading,content=c.content,source_url=d.source_url,campus=d.campus,retrieved_at=d.retrieved_at) for c,d in rows]

def save_reply(db,conversation,query,outcome,message,sources=None,reference=None,offer=False):
    user=append_message(db,conversation,'user',query,sender_id=conversation.owner)
    append_message(db,conversation,'assistant',message,outcome=outcome,
                   sources=[s.model_dump() for s in (sources or [])],
                   details={'user_message_id':user.id,'ticket_reference':reference,
                            'ticket_offer':{'message_id':user.id,'query':query} if offer else None})
    return ChatResponse(conversation_id=conversation.id,user_message_id=user.id,outcome=outcome,message=message,sources=sources or [],ticket_reference=reference,ticket_offer=TicketOffer(message_id=user.id,query=query) if offer else None)

@app.get('/api/conversations')
def conversations(owner: str=Depends(require_access),db: Session=Depends(get_db)):
    rows=db.scalars(select(Conversation).where(Conversation.owner==owner).order_by(Conversation.updated_at.desc()).limit(200)).all()
    return [summary(db,c) for c in rows]

@app.post('/api/conversations')
def new_conversation(body: ConversationCreate,owner: str=Depends(require_access),db: Session=Depends(get_db)):
    existing=db.get(Conversation,str(body.id))
    if existing:
        if existing.owner!=owner:raise HTTPException(404,'Conversation not found.')
        return summary(db,existing)
    row=Conversation(id=str(body.id),owner=owner)
    db.add(row)
    try:db.commit()
    except IntegrityError:
        db.rollback()
        row=db.get(Conversation,str(body.id))
        if not row or row.owner!=owner:raise HTTPException(404,'Conversation not found.')
    return summary(db,row)

@app.get('/api/conversations/{conversation_id}')
def conversation_detail(conversation_id: str,user=Depends(require_user),db: Session=Depends(get_db)):
    return detail(db,conversation_for(db,conversation_id,user))

def generate_reply(body,conversation,db,generator,search,resolver):
    query=body.message.strip()
    if not query:
        raise HTTPException(422,'Enter a question first.')
    messages=recent_messages(db,conversation.id)
    history=[{'role':m.role,'content':m.content} for m in messages]
    pending=pending_question(messages)
    decision=ticket_decision(query)
    if pending and decision is not None:
        if decision:
            ticket=create_ticket(db,conversation.id,pending.content,'Student confirmed a support ticket',pending.id)
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
            sources=list({s.id:s for s in [*sources,*context_sources(db,messages)]}.values())[:8]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503,'Knowledge search is unavailable. Please try again.') from exc
    clarification=clarification_for(resolved.query,sources,history)
    if clarification:
        result=Generation(outcome='clarification',message=clarification,source_ids=[])
    elif sources:
        result=validate_generation(generator.generate(query,sources,history),sources)
    else:
        result=Generation(outcome='unsupported',message='I could not find that information in the approved campus knowledge base.',source_ids=[])
    if result.outcome=='answered' and any(s.source_url for s in sources) and asks_for_price(resolved.query) and not contains_price(result.message):
        result=Generation(outcome='unsupported',message='The requested price is not established by this answer.',source_ids=[])
    if result.outcome=='unsupported':
        return save_reply(db,conversation,query,'needs_staff_confirmation','I couldn’t find an answer in the available campus sources. Would you like me to raise a ticket for student support?',offer=True)
    selected=[s for s in sources if s.id in result.source_ids]
    return save_reply(db,conversation,query,result.outcome,result.message,selected)

@app.post('/api/chat',response_model=ChatResponse)
def chat(body: ChatRequest,owner: str=Depends(allow_chat),db: Session=Depends(get_db),generator=Depends(get_generator),search=Depends(get_retriever),resolver=Depends(get_query_resolver)):
    query=body.message.strip()
    if not query:raise HTTPException(422,'Enter a question first.')
    previous=retry_result(db,owner,body.client_request_id,body.conversation_id,query)
    if previous:return previous
    # Reserve AI capacity before taking the conversation lock; the reservation
    # commits independently of message/provider success and cannot release the lock.
    if body.conversation_id:
        existing=db.scalar(select(Conversation).where(Conversation.id==str(body.conversation_id),Conversation.owner==owner))
        if not existing:raise HTTPException(404,'Conversation not found.')
        ai=existing.state=='ai'
    else:ai=True
    if ai:reserve_ai(db,owner)
    if body.conversation_id:
        conversation=db.scalar(select(Conversation).where(Conversation.id==str(body.conversation_id),Conversation.owner==owner).with_for_update().execution_options(populate_existing=True))
        if not conversation:raise HTTPException(404,'Conversation not found.')
    else:
        conversation=Conversation(owner=owner);db.add(conversation);db.flush()
    previous=retry_result(db,owner,body.client_request_id,body.conversation_id,query)
    if previous:return previous
    if conversation.state=='resolved':raise HTTPException(409,'This conversation is resolved. Reopen it or start a new conversation.')
    if conversation.state!='ai':
        user=append_message(db,conversation,'user',query,sender_id=owner)
        reply=ChatResponse(conversation_id=conversation.id,user_message_id=user.id,outcome='conversation',message='')
    else:
        reply=generate_reply(body,conversation,db,generator,search,resolver)
    remember(db,owner,body.client_request_id,conversation.id,query,reply.model_dump())
    db.commit()
    return reply

@app.post('/api/conversations/{conversation_id}/messages')
def send_message(conversation_id: str,body: MessageRequest,user=Depends(require_user),db: Session=Depends(get_db),generator=Depends(get_generator),search=Depends(get_retriever),resolver=Depends(get_query_resolver)):
    if user.role=='student':
        conversation_for(db,conversation_id,user)
        if not settings().chat_enabled and db.get(Conversation,conversation_id).state=='ai':
            raise HTTPException(503,'Chat is temporarily paused by the project owner.')
        chat(ChatRequest(message=body.message,conversation_id=conversation_id,client_request_id=body.client_request_id),user.id,db,generator,search,resolver)
    else:
        conversation=conversation_for(db,conversation_id,user,lock=True)
        content=body.message.strip()
        if not content:raise HTTPException(422,'Enter a message first.')
        if not retry_result(db,user.id,body.client_request_id,conversation_id,content):
            if conversation.state!='staff_active':raise HTTPException(409,'Start this staff chat before replying.')
            row=append_message(db,conversation,'staff',content,sender_id=user.id)
            remember(db,user.id,body.client_request_id,conversation_id,content,{'message_id':row.id})
            db.commit()
    return detail(db,db.get(Conversation,conversation_id))

@app.post('/api/conversations/{conversation_id}/accept')
def accept_conversation(conversation_id: str,user=Depends(staff),db: Session=Depends(get_db)):
    conversation=conversation_for(db,conversation_id,user,lock=True)
    if conversation.state not in {'waiting_for_staff','staff_active'}:raise HTTPException(409,'This conversation is not waiting for staff.')
    conversation.state='staff_active';conversation.updated_at=now();db.commit()
    return detail(db,conversation)

@app.post('/api/conversations/{conversation_id}/reopen')
def reopen_conversation(conversation_id: str,owner: str=Depends(require_access),db: Session=Depends(get_db)):
    conversation=db.scalar(select(Conversation).where(Conversation.id==conversation_id,Conversation.owner==owner).with_for_update())
    if not conversation:raise HTTPException(404,'Conversation not found.')
    ticket=db.scalar(select(Ticket).where(Ticket.conversation_id==conversation_id).order_by(Ticket.created_at.desc()).limit(1))
    if not ticket:raise HTTPException(409,'No staff handoff exists for this conversation.')
    if conversation.state=='resolved':
        ticket.status='open';conversation.state='waiting_for_staff';conversation.updated_at=now();db.commit()
    return detail(db,conversation)

@app.post('/api/conversations/{conversation_id}/escalate')
def escalate(conversation_id: str,body: EscalationRequest,owner: str=Depends(require_access),db: Session=Depends(get_db)):
    conversation=db.scalar(select(Conversation).where(Conversation.id==conversation_id,Conversation.owner==owner).with_for_update())
    if not conversation:raise HTTPException(404,'Conversation not found.')
    if conversation.state=='resolved':raise HTTPException(409,'Reopen this conversation before requesting staff.')
    target=db.get(Message,str(body.message_id))
    if not target or target.conversation_id!=conversation_id or target.role!='user':
        raise HTTPException(404,'The question to send was not found in this conversation.')
    ticket=create_ticket(db,conversation_id,target.content,'Student confirmed a support ticket',target.id)
    # Persist consent so the next turn no longer sees an unanswered ticket offer.
    confirmation=f'Ticket {ticket.reference} was raised for: {target.content}'
    if not db.scalar(select(Message.id).where(Message.conversation_id==conversation_id,Message.content==confirmation)):
        append_message(db,conversation,'user','Yes, raise a ticket for: '+target.content,sender_id=owner)
        db.flush()
        append_message(db,conversation,'assistant',confirmation,outcome='escalated',details={'ticket_reference':ticket.reference,'user_message_id':target.id})
    db.commit()
    return {'ticket_reference':ticket.reference,'message_id':target.id}

@app.get('/api/staff/tickets',dependencies=[Depends(staff)])
def tickets(status: str=Query('open',pattern='^(open|resolved|all)$'),db: Session=Depends(get_db)):
    stmt=select(Ticket).order_by(Ticket.created_at.desc())
    if status!='all':
        stmt=stmt.where(Ticket.status==status)
    rows=db.scalars(stmt.limit(200)).all()
    # Fetch context for all displayed tickets in one bounded query, rather than
    # one database round trip per row as the queue grows.
    conversations={t.conversation_id for t in rows}
    context={key:[] for key in conversations}
    if conversations:
        ranked=select(Message.conversation_id,Message.role,Message.content,
            func.row_number().over(partition_by=Message.conversation_id,order_by=(Message.created_at.desc(),Message.id.desc())).label('position')).where(Message.conversation_id.in_(conversations)).subquery()
        messages=db.execute(select(ranked).where(ranked.c.position<=80).order_by(ranked.c.conversation_id,ranked.c.position.desc())).mappings()
        for message in messages:
            context[message['conversation_id']].append({'role':message['role'],'content':message['content']})
    return [{'id':t.id,'reference':t.reference,'conversation_id':t.conversation_id,'query':t.query,'reason':t.reason,'status':t.status,'created_at':t.created_at,'messages':context[t.conversation_id]} for t in rows]

@app.patch('/api/staff/tickets/{ticket_id}',dependencies=[Depends(staff)])
def update_ticket(ticket_id: str,body: TicketUpdate,db: Session=Depends(get_db)):
    ticket=db.get(Ticket,ticket_id)
    if not ticket:
        raise HTTPException(404,'Ticket not found.')
    conversation=db.scalar(select(Conversation).where(Conversation.id==ticket.conversation_id).with_for_update())
    if body.status=='open' and db.scalar(select(Ticket.id).where(Ticket.conversation_id==ticket.conversation_id,Ticket.status=='open',Ticket.id!=ticket.id)):
        raise HTTPException(409,'This conversation already has an open ticket.')
    ticket.status=body.status
    conversation.state='resolved' if body.status=='resolved' else 'waiting_for_staff'
    conversation.updated_at=now()
    db.commit()
    return {'id':ticket.id,'status':ticket.status}
