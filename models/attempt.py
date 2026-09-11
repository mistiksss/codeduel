"""Submitted solutions (training and duel)."""

from datetime import datetime, timezone

from extensions import db


class Attempt(db.Model):
    """One submitted program for a task.

    ``status`` is a string such as ``accepted``, ``partially_correct``,
    ``wrong_answer``, ``time_limit``, ``runtime_error``, ``compilation_error``
    or ``testing``. Forfeit placeholders use ``FORFEIT_WIN`` / ``FORFEIT_LOSS``.
    """

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
