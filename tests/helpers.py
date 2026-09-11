"""Shared helpers for application tests."""

from config import TestConfig
from create_app import create_app
from extensions import db
from models import Task, TestCase, User


def make_app():
    """Build a Flask app bound to an empty in-memory database."""
    app, socketio = create_app(TestConfig)
    return app, socketio


def create_user(username, email, password='secret12', **extra):
    """Insert a user with a hashed password and return the instance."""
    from flask import current_app

    password_hash = current_app.bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        **extra,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_task(title='Sum', points=100, time_limit=2, difficulty='easy', cases=None):
    """Insert a task with optional test cases (list of (input, output, hidden))."""
    task = Task(
        title=title,
        description='Add two numbers',
        input_description='Two ints',
        output_description='Their sum',
        difficulty=difficulty,
        points=points,
        time_limit=time_limit,
    )
    db.session.add(task)
    db.session.flush()
    if cases is None:
        cases = [('1 2', '3', False)]
    for input_data, expected_output, is_hidden in cases:
        db.session.add(TestCase(
            task_id=task.id,
            input_data=input_data,
            expected_output=expected_output,
            is_hidden=is_hidden,
        ))
    db.session.commit()
    return task


def login(client, email, password='secret12'):
    """Submit the login form and follow the redirect."""
    return client.post(
        '/login',
        data={'email': email, 'password': password},
        follow_redirects=False,
    )
