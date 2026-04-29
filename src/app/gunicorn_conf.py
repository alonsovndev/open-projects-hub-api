import os

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8080")
bind_env = os.getenv("BIND")
loglevel = os.getenv("LOG_LEVEL", "info")
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")

bind = bind_env if bind_env else f"{host}:{port}"

# Gunicorn config variables
# These variables are used by Gunicorn when running `gunicorn -c src/gunicorn_conf.py ...`
# bind, loglevel, workers, worker_class can be overridden via environment variables above
