"""Programming tasks and their hidden/public test cases."""

from extensions import db


class TestCase(db.Model):
    """Single input/output pair used to judge a solution.

    ``is_hidden`` controls whether the case is shown as a sample on the
    arena page. Judging always runs every case for the task.
    """

    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.ForeignKey('tasks.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer, default=10)


class Task(db.Model):
    """A coding problem that can be solved in training or in a duel."""

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    input_description = db.Column(db.Text)
    output_description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    points = db.Column(db.Integer, default=20)
    time_limit = db.Column(db.Integer, default=2)
    test_cases = db.relationship(
        'TestCase',
        backref='task',
        lazy=True,
        cascade='all, delete-orphan',
    )
