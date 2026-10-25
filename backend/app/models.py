from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, JSON, Integer, BigInteger, UniqueConstraint, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

def new_id():
    return str(uuid.uuid4())

def now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)

class LoginSession(Base):
    __tablename__ = 'login_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    campus: Mapped[str | None] = mapped_column(String(40), nullable=True)
    retrieved_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

class Chunk(Base):
    __tablename__ = 'chunks'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    heading: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    owner: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(30), default='ai')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    next_sequence: Mapped[int] = mapped_column(Integer, default=1)

class RequestBudget(Base):
    __tablename__ = 'request_budgets'
    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    window: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (UniqueConstraint('conversation_id', 'sequence', name='uq_message_sequence'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sender_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Submission(Base):
    __tablename__ = 'submissions'
    __table_args__ = (UniqueConstraint('user_id', 'request_id', name='uq_submission_request'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    request_id: Mapped[str] = mapped_column(String(36))
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'))
    content: Mapped[str] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON)

class Ticket(Base):
    __tablename__ = 'tickets'
    __table_args__ = (Index('uq_open_ticket_conversation', 'conversation_id', unique=True,
                           postgresql_where=text("status = 'open'"), sqlite_where=text("status = 'open'")),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(24), unique=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'), index=True)
    message_id: Mapped[str | None] = mapped_column(ForeignKey('messages.id'), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default='open', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
