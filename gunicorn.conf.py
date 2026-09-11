import os

bind = os.environ.get('GUNICORN_BIND') or f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120
keepalive = 5

errorlog = '-'
accesslog = '-'
loglevel = 'info'

max_requests = 1000
max_requests_jitter = 50

# eventlet + Socket.IO: one worker unless Redis is configured as a message queue.
preload_app = False
