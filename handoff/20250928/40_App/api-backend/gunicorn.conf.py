"""
Gunicorn configuration file for MorningAI API Backend
"""
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

workers = int(os.getenv('GUNICORN_WORKERS', '4'))
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
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

proc_name = 'morningai-api'

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None


reload = os.getenv('GUNICORN_RELOAD', 'false').lower() == 'true'
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
