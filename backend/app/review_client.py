"""Authenticate live regression clients without printing credentials or tokens."""
from .config import settings

def authenticate(client):
    response=client.post('/api/auth/session',json={'password':settings().review_password})
    response.raise_for_status()
    client.headers['Authorization']='Bearer '+response.json()['access_token']
