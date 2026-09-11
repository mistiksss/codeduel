"""Liveness endpoint and HTTP error pages."""

from flask import jsonify, render_template
from sqlalchemy import text

from extensions import db
from utils.utc import utc_now


def register_health_routes(app):
    """Register ``/health`` and the 429 error page."""

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template('error_429.html'), 429

    @app.route('/health')
    def health_check():
        try:
            try:
                db.session.execute(text('SELECT 1'))
                database_status = 'connected'
            except Exception:
                database_status = 'disconnected'

            return jsonify({
                'status': 'healthy',
                'database': database_status,
                'timestamp': utc_now().isoformat(),
            })
        except Exception as exc:
            return jsonify({'status': 'unhealthy', 'error': str(exc)}), 500
