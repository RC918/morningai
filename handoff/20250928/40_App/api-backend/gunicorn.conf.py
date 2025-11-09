"""
Gunicorn configuration file for MorningAI API Backend
"""
# Fix deployment import path: Add repo root to sys.path before importing common
# This is required because gunicorn may run from api-backend/ directory where common/ is not visible
from pathlib import Path
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
_bootstrap_logger = logging.getLogger(__name__)

if 'REPO_ROOT' in os.environ:
    repo_root = os.environ['REPO_ROOT']
    if repo_root and repo_root.endswith('/common'):
        repo_root = str(Path(repo_root).parent)
        if os.getenv('DEBUG_IMPORTS'):
            _bootstrap_logger.info(f"⚠️  REPO_ROOT misconfigured as common dir, corrected to: {repo_root}")
    if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
        sys.path.insert(0, repo_root)
        if os.getenv('DEBUG_IMPORTS'):
            _bootstrap_logger.info(f"✅ sys.path bootstrap: REPO_ROOT={repo_root}")

if 'PYTHONPATH' in os.environ:
    pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
    for entry in reversed(pythonpath_entries):
        if entry and os.path.isdir(entry) and entry not in sys.path:
            sys.path.insert(0, entry)
            if os.getenv('DEBUG_IMPORTS'):
                _bootstrap_logger.info(f"✅ sys.path bootstrap: PYTHONPATH entry={entry}")

config_file_path = Path(__file__).resolve()
for parent in [config_file_path] + list(config_file_path.parents):
    if (parent / 'pyproject.toml').exists() or (parent / '.git').exists() or (parent / 'env.schema.yaml').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
            if os.getenv('DEBUG_IMPORTS'):
                _bootstrap_logger.info(f"✅ sys.path bootstrap: marker file at {parent}")
        break

if os.getenv('DEBUG_IMPORTS'):
    _bootstrap_logger.info(f"Final sys.path (first 3): {sys.path[:3]}")

import multiprocessing
from common.config.settings import settings

bind = f"0.0.0.0:{settings.port or 8000}"
backlog = 2048

workers = settings.gunicorn_workers or 4
worker_class = 'sync'  # Use 'gevent' or 'eventlet' for async if needed
worker_connections = 1000
threads = 2  # Threads per worker (only for gthread worker class)

max_requests = 1000  # Restart workers after N requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to avoid all workers restarting together
timeout = 120  # Worker timeout in seconds
graceful_timeout = 30  # Time to wait for graceful shutdown
keepalive = 5  # Seconds to wait for requests on Keep-Alive connections

accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = settings.gunicorn_log_level or 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

proc_name = 'morningai-api'

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None


reload = settings.gunicorn_reload or False
reload_engine = 'auto'

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info(f"Starting Gunicorn with {workers} workers")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Gunicorn workers")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn server is ready. Spawning workers")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")

def worker_int(worker):
    """Called just after a worker received INT or QUIT signal."""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker received SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT signal")
