"""HTTP routes grouped by domain (pages, auth, solutions, matches)."""

from routes.auth import auth_bp
from routes.health import register_health_routes
from routes.match import match_bp
from routes.pages import register_page_routes
from routes.solutions import register_solution_routes


def register_routes(app, limiter=None):
    """Attach all blueprints and app-level views to ``app``.

    Page and solution views are registered on the application itself so
    existing ``url_for('tasks')`` / ``url_for('profile')`` calls in
    templates keep working.
    """
    register_page_routes(app)
    register_solution_routes(app, limiter=limiter)
    register_health_routes(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(match_bp)

    if limiter:
        from routes.auth import login as auth_login_view

        app.view_functions['auth.login'] = limiter.limit('5 per minute')(auth_login_view)
