from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegisterForm, LoginForm

auth_bp = Blueprint('auth', __name__)


def get_bcrypt():
    from flask import current_app
    return getattr(current_app, 'bcrypt', None) or current_app.extensions.get('bcrypt')


def get_matchmaking_system():
    from flask import current_app
    return getattr(current_app, 'matchmaking_system', None)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from flask import request
    bcrypt = get_bcrypt()
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.is_online = True
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('main_page'))
    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    bcrypt = get_bcrypt()
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        new_user.is_online = True
        new_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        return redirect(url_for('auth.onboarding'))
    return render_template('reg.html', form=form)


@auth_bp.route('/onboarding', methods=['GET'])
@login_required
def onboarding():
    if getattr(current_user, 'onboarding_completed', False):
        return redirect(url_for('main_page'))
    return render_template('onboarding.html')


@auth_bp.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    current_user.last_seen = datetime.now(timezone.utc)
    mms = get_matchmaking_system()
    if mms:
        mms.cancel_search(current_user.id)
    db.session.commit()
    logout_user()
    return redirect(url_for('main'))