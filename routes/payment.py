"""Payment and premium subscription routes."""
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from extensions import db

payment_bp = Blueprint('payment', __name__, url_prefix='')


@payment_bp.route('/pricing')
def pricing():
    """Pricing page (landing for non-Pro users)."""
    is_premium = current_user.is_authenticated and hasattr(current_user, 'has_premium') and current_user.has_premium()
    return render_template('pricing.html', is_premium=is_premium)


@payment_bp.route('/api/payment/mock', methods=['POST'])
@login_required
def mock_payment():
    """Mock payment: set premium for 30 days (test only)."""
    try:
        now = datetime.now(timezone.utc)
        current_user.is_premium = True
        current_user.premium_until = now + timedelta(days=30)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Premium activated for 30 days',
            'premium_until': current_user.premium_until.isoformat() if current_user.premium_until else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
