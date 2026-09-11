"""User account and rating statistics."""

from datetime import datetime, timezone

from flask_login import UserMixin

from extensions import db


class User(db.Model, UserMixin):
    """Registered player.

    Rating fields (``elo``, ``wins``, ``losses``, ``draws``, ``best_elo``,
    ``games_played``, ``current_streak``) are updated when a match is
    finalized via :func:`services.match_service.apply_match_result`.
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    elo = db.Column(db.Integer, default=1000)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    best_elo = db.Column(db.Integer, default=1000)
    games_played = db.Column(db.Integer, default=0)
    title = db.Column(db.String(50), nullable=False, default='Новичок')
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    onboarding_completed = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.String(20), default='python')
    experience_level = db.Column(db.String(20), default='novice')
    current_streak = db.Column(db.Integer, default=0)
