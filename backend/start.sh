#!/bin/sh
set -eu
alembic upgrade head
python -m app.provision_accounts
# Fail before serving if the baked-in embedding model is unavailable.
python -c 'from app.retrieval import embed; assert len(embed(["startup check"])[0]) == 384'
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 1 --ws-max-size 1024 --proxy-headers
