"""Conversation authorization, ordering and transaction-local message helpers."""
from fastapi import HTTPException
from sqlalchemy import select
from .models import Conversation, Message, Ticket, Submission, now

STATES={'ai','waiting_for_staff','staff_active','resolved'}

def conversation_for(db,cid,user,lock=False):
    stmt=select(Conversation).where(Conversation.id==cid)
    if lock:stmt=stmt.with_for_update()
    conversation=db.scalar(stmt)
    allowed=conversation and (conversation.owner==user.id if user.role=='student' else
                             db.scalar(select(Ticket.id).where(Ticket.conversation_id==cid).limit(1)))
    if not allowed:raise HTTPException(404,'Conversation not found.')
    return conversation

def append_message(db,conversation,role,content,sender_id=None,outcome=None,sources=None,details=None):
    row=Message(conversation_id=conversation.id,role=role,content=content,sender_id=sender_id,
                outcome=outcome,sources=sources or [],details=details or {},sequence=conversation.next_sequence,created_at=now())
    conversation.next_sequence+=1
    conversation.updated_at=now()
    db.add(row);db.flush()
    return row

def summary(db,conversation):
    first=db.scalar(select(Message.content).where(Message.conversation_id==conversation.id,Message.role=='user').order_by(Message.sequence,Message.created_at).limit(1))
    return {'id':conversation.id,'state':conversation.state,'title':(first or 'New conversation')[:100],
            'created_at':conversation.created_at,'updated_at':conversation.updated_at}

def detail(db,conversation):
    rows=db.scalars(select(Message).where(Message.conversation_id==conversation.id).order_by(Message.sequence,Message.created_at,Message.id)).all()
    tickets=db.scalars(select(Ticket).where(Ticket.conversation_id==conversation.id).order_by(Ticket.created_at.desc())).all()
    return {**summary(db,conversation),'conversation_id':conversation.id,
            'ticket_reference':tickets[0].reference if tickets else None,
            'messages':[{'id':m.id,'role':m.role,'sender_id':m.sender_id,'content':m.content,
                         'outcome':m.outcome,'sources':m.sources,'created_at':m.created_at,
                         'sequence':m.sequence,**m.details} for m in rows]}

def retry_result(db,user_id,request_id,cid,content):
    if not request_id:return None
    previous=db.scalar(select(Submission).where(Submission.user_id==user_id,Submission.request_id==str(request_id)))
    if previous:
        if previous.content!=content or (cid and previous.conversation_id!=str(cid)):
            raise HTTPException(409,'This request ID was already used for a different message.')
        return previous.result
    return None

def remember(db,user_id,request_id,cid,content,result):
    if request_id:
        db.add(Submission(user_id=user_id,request_id=str(request_id),conversation_id=cid,content=content,result=result))
