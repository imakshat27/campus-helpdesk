from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .config import settings

def normalize_url(url: str):
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg://' + url[len('postgres://'):]
    elif url.startswith('postgresql://'):
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    return url

@lru_cache
def engine():
    url = settings().database_url
    if not url:
        raise HTTPException(503, 'Database is not configured. Set DATABASE_URL on the backend.')
    return create_engine(normalize_url(url), pool_pre_ping=True, connect_args={'connect_timeout': 10})

def get_db():
    with Session(engine()) as db:
        yield db
