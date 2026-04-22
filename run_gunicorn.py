"""Gunicorn entry point — для gunicorn.conf.py."""
from create_app import create_app

app, socketio = create_app()