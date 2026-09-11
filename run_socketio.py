"""Socket.IO runner for eventlet — used locally and on Render."""

import os

import eventlet
eventlet.monkey_patch()

from dotenv import load_dotenv

load_dotenv()

from create_app import create_app

app, socketio = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
