"""Gunicorn production configuration file for E-Invoice FastAPI application.
Runs Uvicorn worker processes with multi-core load balancing.
"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes (2 * CPU cores + 1)
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = "einvoice_fastapi"

# Logging configuration
accesslog = "/var/log/einvoice/access.log"
errorlog = "/var/log/einvoice/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# Server mechanics
daemon = False
pidfile = "/var/run/einvoice.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None
