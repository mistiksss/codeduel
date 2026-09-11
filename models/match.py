"""Duel matches, per-player results and the matchmaking queue."""

from datetime import datetime, timezone

from extensions import db


class Match(db.Model):
    """A 1v1 duel between ``user_id`` and ``opponent_id`` on one task.

    ``result`` is stored from the ``user_id`` player's point of view:
    ``win``, ``loss``, ``draw``, or ``None`` while the duel is in progress.

    Rating deltas are stored on this row so history views do not depend
    on later Elo changes.
    """

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
    """Latest judged submission of one player inside a match."""

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
    """Players currently searching for an opponent."""

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
