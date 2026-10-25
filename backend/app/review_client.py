"""Authenticate regression clients without printing credentials or cookies."""
import httpx
from .config import settings
from .access import COOKIE

def authenticate(client, role='student'):
    config=settings()
    client.headers['Origin']=config.cors_origins[0]
    response=client.post('/api/auth/session',json={
        'username':getattr(config,role+'_username'),
        'password':getattr(config,role+'_password')})
    response.raise_for_status()

def staff_headers(client):
    """Get a staff cookie without replacing the student's active session."""
    previous=httpx.Cookies(client.cookies)
    try:
        authenticate(client,'staff')
        return {'Cookie':COOKIE+'='+client.cookies.get(COOKIE)}
    finally:
        client.cookies.clear()
        client.cookies.update(previous)
