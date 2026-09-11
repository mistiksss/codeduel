"""Gunicorn entry point — used by gunicorn.conf.py and systemd."""

import eventlet
eventlet.monkey_patch()

from create_app import create_app

app, socketio = create_app()
