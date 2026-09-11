"""Gunicorn entry point — used by gunicorn.conf.py and codeduel.service."""

from create_app import create_app

app, socketio = create_app()
