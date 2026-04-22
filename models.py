from datetime import datetime, timezone

from flask_login import UserMixin

from extensions import db


class User(db.Model, UserMixin):
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
    title = db.Column(db.String(50), nullable=False, default="Новичок")
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    onboarding_completed = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.String(20), default='python')
    experience_level = db.Column(db.String(20), default='novice')
    current_streak = db.Column(db.Integer, default=0)


class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.ForeignKey('tasks.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer, default=10)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    input_description = db.Column(db.Text)
    output_description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    points = db.Column(db.Integer, default=20)
    time_limit = db.Column(db.Integer, default=2)
    test_cases = db.relationship('TestCase', backref='task', lazy=True, cascade='all, delete-orphan')


class Attempt(db.Model):
    __tablename__ = 'attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.ForeignKey('tasks.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    execution_time = db.Column(db.Float)
    tests_passed = db.Column(db.Integer)
    total_tests = db.Column(db.Integer)
    score = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='attempts')
    task = db.relationship('Task', backref='attempts')


class Match(db.Model):
    __tablename__ = 'matches'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    opponent_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.ForeignKey('tasks.id'), nullable=False)
    result = db.Column(db.String(10))
    user_rating_change = db.Column(db.Integer, default=0)
    opponent_rating_change = db.Column(db.Integer, default=0)
    match_duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)

    user = db.relationship('User', foreign_keys=[user_id], backref='matches_as_user')
    opponent = db.relationship('User', foreign_keys=[opponent_id], backref='matches_as_opponent')
    task = db.relationship('Task', backref='matches')


class MatchResult(db.Model):
    __tablename__ = 'match_results'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.ForeignKey('matches.id'), nullable=False)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    attempt_id = db.Column(db.ForeignKey('attempts.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    tests_passed = db.Column(db.Integer, default=0)
    total_tests = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    match = db.relationship('Match', backref='detailed_results')
    user = db.relationship('User', backref='match_results')
    attempt = db.relationship('Attempt', backref='match_result')


class MatchmakingQueue(db.Model):
    __tablename__ = 'matchmaking_queue'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    elo = db.Column(db.Integer, nullable=False)
    task_id = db.Column(db.ForeignKey('tasks.id'), nullable=True)
    difficulty = db.Column(db.String(20))
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_ping = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='searching')

    user = db.relationship('User', backref='matchmaking_entries')
    task = db.relationship('Task', backref='matchmaking_entries')