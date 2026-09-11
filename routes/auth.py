"""Authentication: login, registration, onboarding, logout."""

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms import LoginForm, RegisterForm
from models import User
from utils.extensions_access import get_bcrypt, get_matchmaking_system
from utils.utc import utc_now

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log in with email/password and mark the user online."""
    bcrypt = get_bcrypt()
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.is_online = True
            user.last_seen = utc_now()
            db.session.commit()
            return redirect(url_for('main_page'))
    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Create an account, log the user in and send them to onboarding."""
    bcrypt = get_bcrypt()
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        new_user.is_online = True
        new_user.last_seen = utc_now()
        db.session.commit()
        return redirect(url_for('auth.onboarding'))
    return render_template('reg.html', form=form)


@auth_bp.route('/onboarding', methods=['GET'])
@login_required
def onboarding():
    """First-run language picker. Skipped once onboarding is completed."""
    if getattr(current_user, 'onboarding_completed', False):
        return redirect(url_for('main_page'))
    return render_template('onboarding.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Mark the user offline, leave matchmaking and end the session."""
    current_user.is_online = False
    current_user.last_seen = utc_now()
    matchmaking = get_matchmaking_system()
    if matchmaking:
        matchmaking.cancel_search(current_user.id)
    db.session.commit()
    logout_user()
    return redirect(url_for('main'))
