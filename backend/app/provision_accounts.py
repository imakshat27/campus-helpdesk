"""Provision exactly one student and one staff account. Never log credentials."""
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from .access import hasher
from .config import settings
from .db import engine
from .models import User, LoginSession

def provision(db, config):
    accounts = [(role, getattr(config, role + '_username').strip(), getattr(config, role + '_password'))
                for role in ('student', 'staff')]
    if any(not username or len(username) > 100 or len(password) < 8 or len(password) > 1024
           for _, username, password in accounts):
        raise ValueError('Set both account usernames and passwords (8–1024 characters; use at least 16 for new credentials) privately before provisioning.')
    if accounts[0][1] == accounts[1][1]:
        raise ValueError('Student and staff usernames must differ.')
    for role, username, password in accounts:
        user = db.scalar(select(User).where(User.role == role))
        if user is None:
            db.add(User(username=username, role=role, password_hash=hasher.hash(password)))
        else:
            from argon2.exceptions import VerificationError
            try:
                unchanged = hasher.verify(user.password_hash, password)
            except VerificationError:
                unchanged = False
            if not unchanged or user.username != username:
                db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
                user.username = username
                user.password_hash = hasher.hash(password)
    db.commit()

if __name__ == '__main__':
    with Session(engine()) as db:
        provision(db, settings())
    print('Student and staff accounts provisioned. Credentials were not displayed.')
