"""Decorators and helpers for premium/access control."""
from functools import wraps

from flask import redirect, url_for
from flask_login import login_required, current_user


def premium_required(f):
    """Decorator: redirect to /pricing if user is not Pro."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('payment.pricing'))
        if not (hasattr(current_user, 'has_premium') and current_user.has_premium()):
            return redirect(url_for('payment.pricing'))
        return f(*args, **kwargs)
    return decorated
