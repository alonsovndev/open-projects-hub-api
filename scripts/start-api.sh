#!/usr/bin/env bash

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec gunicorn -k uvicorn.workers.UvicornWorker -c ./src/app/gunicorn_conf.py src.main:app