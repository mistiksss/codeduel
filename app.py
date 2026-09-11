"""Development entry point with eventlet WebSocket support.

Production uses ``run_gunicorn.py`` / ``run_socketio.py``, which also call
:func:`create_app.create_app`.
"""

import os

import eventlet
eventlet.monkey_patch()

from create_app import create_app
from services.presence import start_presence_worker

app, socketio = create_app()

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_presence_worker(app)
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
