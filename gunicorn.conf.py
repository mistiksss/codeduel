import multiprocessing

bind = "127.0.0.1:5000"
workers = 2
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
keepalive = 5

errorlog = "-"
accesslog = "-"
loglevel = "info"

max_requests = 1000
max_requests_jitter = 50

preload_app = False