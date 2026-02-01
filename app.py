from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo
from flask_bcrypt import Bcrypt
from sqlalchemy import desc, or_, func
from datetime import datetime, timezone, timedelta
from executor import run_code
import os
import time
import math
import threading
import traceback

def to_utc_aware(dt):
    if dt is None:
        return None
    if getattr(dt, 'tzinfo', None) is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def normalize_match_started_at(match, now_utc=None):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if not getattr(match, 'started_at', None):
        match.started_at = to_utc_aware(getattr(match, 'created_at', None)) or now_utc
        return match.started_at

    started_at = to_utc_aware(match.started_at)
    if started_at > (now_utc + timedelta(seconds=60)):
        fallback = to_utc_aware(getattr(match, 'created_at', None)) or now_utc
        started_at = min(started_at, fallback)

    if started_at != match.started_at:
        match.started_at = started_at

    return started_at


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:54321@localhost:5432/code_duel'
app.config['SECRET_KEY'] = "ea895771cd548603ffeb0f919568488deede3e855285883bb5c55c6b484c13cc"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['CODE_EXECUTION_TIMEOUT'] = 5
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


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

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_active_match_to_templates():
    try:
        if current_user.is_authenticated:
            m = get_active_match_for_user(current_user.id)
            return {
                'active_match': m,
                'active_match_id': (m.id if m else None),
            }
    except Exception:
        pass
    return {'active_match': None, 'active_match_id': None}


class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
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
    difficulty_level = db.Column(db.Integer)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    points = db.Column(db.Integer, default=20)
    time_limit = db.Column(db.Integer, default=2)
    memory_limit = db.Column(db.Integer, default=256)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    example = db.Column(db.Text)
    answer = db.Column(db.Text)
    test_cases = db.relationship('TestCase', backref='task', lazy=True, cascade='all, delete-orphan')


class Attempt(db.Model):
    __tablename__ = 'attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    execution_time = db.Column(db.Float)
    memory_used = db.Column(db.Integer)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opponent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
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
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempts.id'), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    elo = db.Column(db.Integer, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_ping = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='searching')  # searching, matched, cancelled

    user = db.relationship('User', backref='matchmaking_entries')
    task = db.relationship('Task', backref='matchmaking_entries')


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    confirm_password = PasswordField(validators=[InputRequired(), EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("Это имя пользователя уже занято. Пожалуйста, выберите другое.")


class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    submit = SubmitField('Войти')

duel_max_time = 7200


def _apply_match_result(match: Match, result: str):
    if match is None or match.result is not None:
        return

    if result not in {'win', 'loss', 'draw'}:
        raise ValueError('Invalid match result')

    now_utc = datetime.now(timezone.utc)

    started_at = normalize_match_started_at(match, now_utc=now_utc)

    user = db.session.get(User, match.user_id)
    opp = db.session.get(User, match.opponent_id)
    if not user or not opp:
        raise RuntimeError('Users not found for match')

    match.result = result

    if result == 'win':
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 1)
        user.wins += 1
        opp.losses += 1
    elif result == 'loss':
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0)
        user.losses += 1
        opp.wins += 1
    else:  # draw
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0.5)
        user.draws += 1
        opp.draws += 1

    match.user_rating_change = new_user_elo - user.elo
    match.opponent_rating_change = new_opp_elo - opp.elo
    user.elo = new_user_elo
    opp.elo = new_opp_elo

    user.games_played += 1
    opp.games_played += 1

    match.ended_at = now_utc
    ended_at = to_utc_aware(match.ended_at)
    started_at = normalize_match_started_at(match, now_utc=ended_at)
    duration = int((ended_at - started_at).total_seconds()) if started_at and ended_at else 0
    match.match_duration = max(0, duration)

    if user.elo > user.best_elo:
        user.best_elo = user.elo
    if opp.elo > opp.best_elo:
        opp.best_elo = opp.elo

    db.session.commit()


def get_active_match_for_user(user_id: int):
    match = (Match.query.filter(
        or_(Match.user_id == user_id, Match.opponent_id == user_id),
        Match.result == None
    ).order_by(Match.created_at.desc()).first())

    if not match:
        return None

    if not match.started_at:
        match.started_at = to_utc_aware(match.created_at) or datetime.now(timezone.utc)
        db.session.commit()

    finalize_match_if_needed(match)
    db.session.refresh(match)

    return match if match.result is None else None

def get_task_max_score(task_id: int) -> int:
    task = db.session.get(Task, int(task_id))
    return int(task.points or 0) if task else 0

def finalize_match_if_needed(match: Match):
    if match is None or match.result is not None:
        return
    now_utc = datetime.now(timezone.utc)
    started_at = normalize_match_started_at(match, now_utc=now_utc)
    db.session.commit()

    task_max = get_task_max_score(match.task_id)

    r1 = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
    r2 = MatchResult.query.filter_by(match_id=match.id, user_id=match.opponent_id).first()

    s1 = (r1.score if r1 else 0) or 0
    s2 = (r2.score if r2 else 0) or 0

    tp1 = (r1.tests_passed if r1 else 0) or 0
    tp2 = (r2.tests_passed if r2 else 0) or 0

    t1 = (r1.execution_time if r1 and r1.execution_time is not None else 10**9)
    t2 = (r2.execution_time if r2 and r2.execution_time is not None else 10**9)

    user = db.session.get(User, match.user_id)
    opp = db.session.get(User, match.opponent_id)

    full1 = bool(r1 and (r1.total_tests or 0) > 0 and (r1.tests_passed or 0) == (r1.total_tests or 0))
    full2 = bool(r2 and (r2.total_tests or 0) > 0 and (r2.tests_passed or 0) == (r2.total_tests or 0))

    if full1 or full2:
        if full1 and not full2:
            match.result = 'win'
        elif full2 and not full1:
            match.result = 'loss'
        else:
            if t1 < t2:
                match.result = 'win'
            elif t2 < t1:
                match.result = 'loss'
            else:
                match.result = 'draw'

    if match.result is None:
        started_at = normalize_match_started_at(match, now_utc=now_utc)
        elapsed = int((now_utc - started_at).total_seconds()) if started_at else 0
        if elapsed >= duel_max_time:
            if tp1 > tp2:
                match.result = 'win'
            elif tp2 > tp1:
                match.result = 'loss'
            else:
                if s1 > s2:
                    match.result = 'win'
                elif s2 > s1:
                    match.result = 'loss'
                else:
                    if t1 < t2:
                        match.result = 'win'
                    elif t2 < t1:
                        match.result = 'loss'
                    else:
                        match.result = 'draw'

    if match.result is None:
        return

    if match.result == 'win':
        new_user_elo, _new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 1)
        user.wins += 1
        opp.losses += 1
    elif match.result == 'loss':
        new_user_elo, _new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0)
        user.losses += 1
        opp.wins += 1
    else:  # draw
        new_user_elo, _new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0.5)
        user.draws += 1
        opp.draws += 1

    match.user_rating_change = new_user_elo - user.elo
    match.opponent_rating_change = 0

    user.elo = new_user_elo

    user.games_played += 1
    opp.games_played += 1

    match.ended_at = now_utc
    ended_at = to_utc_aware(match.ended_at)
    started_at = normalize_match_started_at(match, now_utc=ended_at)
    duration = int((ended_at - started_at).total_seconds()) if started_at and ended_at else 0
    match.match_duration = max(0, duration)

    if user.elo > user.best_elo:
        user.best_elo = user.elo

    db.session.commit()

class MatchmakingSystem:
    def __init__(self):
        self.search_lock = threading.Lock()
        self.ELO_RANGE = 300
        self.MAX_SEARCH_TIME = 300

    def find_opponent(self, user_id, user_elo, difficulty=None):
        with self.search_lock:
            try:
                print(f"Поиск противника для пользователя {user_id} (ELO: {user_elo})")
                self._cleanup_old_entries()

                online_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
                online_filter = or_(User.is_online == True, User.last_seen >= online_cutoff)


                if difficulty and difficulty != 'any':
                    opponent = MatchmakingQueue.query.filter(
                        MatchmakingQueue.user_id != user_id,
                        MatchmakingQueue.status == 'searching',
                        MatchmakingQueue.difficulty == difficulty,
                        MatchmakingQueue.elo.between(user_elo - self.ELO_RANGE, user_elo + self.ELO_RANGE),
                        online_filter
                    ).join(User, MatchmakingQueue.user_id == User.id).order_by(
                        db.func.abs(MatchmakingQueue.elo - user_elo),
                        MatchmakingQueue.joined_at
                    ).first()

                    if opponent:
                        print(f"Найден оппонент {opponent.user_id} для пользователя {user_id} (difficulty={difficulty})")
                        return self._create_match(user_id, opponent.user_id, difficulty)

                opponent = MatchmakingQueue.query.filter(
                    MatchmakingQueue.user_id != user_id,
                    MatchmakingQueue.status == 'searching',
                    MatchmakingQueue.elo.between(user_elo - self.ELO_RANGE, user_elo + self.ELO_RANGE),
                    online_filter
                ).join(User, MatchmakingQueue.user_id == User.id).order_by(
                    db.func.abs(MatchmakingQueue.elo - user_elo),
                    MatchmakingQueue.joined_at
                ).first()

                if opponent:
                    print(f"Найден оппонент {opponent.user_id} для пользователя {user_id} (difficulty={difficulty})")
                    return self._create_match(user_id, opponent.user_id, difficulty)

                opponent = MatchmakingQueue.query.filter(
                    MatchmakingQueue.user_id != user_id,
                    MatchmakingQueue.status == 'searching',
                    online_filter
                ).join(User, MatchmakingQueue.user_id == User.id).order_by(
                    MatchmakingQueue.joined_at
                ).first()

                if opponent:
                    print(f"Найден оппонент {opponent.user_id} для пользователя {user_id} (difficulty={difficulty})")
                    return self._create_match(user_id, opponent.user_id, difficulty)
                return self._add_to_queue(user_id, user_elo, difficulty)

            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при поиске противника: {e}")
                raise e

    def _get_random_task_by_difficulty(self, difficulty):
        try:
            if difficulty == 'any' or not difficulty:
                task = Task.query.order_by(db.func.random()).first()
            else:
                task = Task.query.filter_by(difficulty=difficulty).order_by(db.func.random()).first()

            return task.id if task else None
        except Exception as e:
            print(f"Ошибка при выборе случайной задачи: {e}")
            return None

    def _create_match(self, user1_id, user2_id, difficulty):
        try:
            task_id = self._get_random_task_by_difficulty(difficulty)
            if not task_id:
                task_id = self._get_random_task_by_difficulty('any')
            if not task_id:
                raise Exception("No tasks in database")

            task = db.session.get(Task, task_id)
            if user1_id < user2_id:
                db_user_id, db_opponent_id = user1_id, user2_id
            else:
                db_user_id, db_opponent_id = user2_id, user1_id

            MatchmakingQueue.query.filter(
                MatchmakingQueue.user_id.in_([user1_id, user2_id]),
                MatchmakingQueue.status == 'searching'
            ).update({'status': 'matched'})

            # Создаем матч
            match = Match(
                user_id=db_user_id,
                opponent_id=db_opponent_id,
                task_id=task_id,
                created_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                result=None
            )

            db.session.add(match)
            db.session.commit()

            print(f"Матч создан id={match.id}, task_id={task_id}, users=({db_user_id},{db_opponent_id})")

            opponent_user = db.session.get(User, user2_id)

            return {
                'success': True,
                'match_found': True,
                'match_id': match.id,
                'opponent_id': opponent_user.id,
                'opponent': {
                    'id': opponent_user.id,
                    'username': opponent_user.username,
                    'elo': opponent_user.elo
                },
                'task_id': task_id,
                'task_title': task.title if task else 'Unknown Task',
                'difficulty': difficulty,
                'message': 'Соперник найден!'
            }

        except Exception as e:
            db.session.rollback()
            raise e

    def _add_to_queue(self, user_id, user_elo, difficulty):
        try:
            # Проверяем, не в очереди ли уже пользователь
            existing = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching'
            ).first()

            if existing:
                existing.last_ping = datetime.now(timezone.utc)
                db.session.commit()

                return {
                    'success': True,
                    'in_queue': True,
                    'queue_id': existing.id,
                    'message': 'Вы уже в очереди поиска'
                }

            # Добавляем в очередь
            queue_entry = MatchmakingQueue(
                user_id=user_id,
                elo=user_elo,
                task_id=None,
                difficulty=difficulty,
                status='searching',
                joined_at=datetime.now(timezone.utc),
                last_ping=datetime.now(timezone.utc)
            )

            db.session.add(queue_entry)
            db.session.commit()

            print(f"Пользователь {user_id} добавлен в очередь поиска")

            return {
                'success': True,
                'in_queue': True,
                'queue_id': queue_entry.id,
                'message': 'Ожидание соперника...'
            }

        except Exception as e:
            db.session.rollback()
            raise e

    def _cleanup_old_entries(self):
        stale_before = datetime.now(timezone.utc) - timedelta(seconds=self.MAX_SEARCH_TIME)
        MatchmakingQueue.query.filter(
            MatchmakingQueue.last_ping < stale_before,
            MatchmakingQueue.status == 'searching'
        ).delete()

        db.session.commit()

    def cancel_search(self, user_id):
        with self.search_lock:
            deleted = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching'
            ).delete()
            return deleted > 0

    def ping_queue(self, user_id):
        try:
            updated = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching'
            ).update({'last_ping': datetime.now(timezone.utc)})

            db.session.commit()
            return updated > 0

        except Exception as e:
            db.session.rollback()
            return False

    def get_queue_stats(self, user_id):
        try:
            five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

            total_in_queue = MatchmakingQueue.query.filter_by(
                status='searching'
            ).join(User, MatchmakingQueue.user_id == User.id).filter(
                or_(User.is_online == True, User.last_seen >= five_minutes_ago)
            ).count()

            return {'total_players': total_in_queue}

        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {'total_players': 0}

    def _estimate_wait_time(self, total_players, similar_players):
        if similar_players > 0:
            return max(5, 60 // (similar_players + 1))
        elif total_players > 0:
            return max(10, 120 // (total_players + 1))
        else:
            return 30

matchmaking_system = MatchmakingSystem()

def normalize_output(output):
    if output is None:
        return ""
    return output.strip().replace('\r\n', '\n')


def validate_solution(task_id, code, language):
    task = db.session.get(Task, int(task_id))
    if not task:
        return {'error': 'Task not found'}

    test_cases = TestCase.query.filter_by(task_id=task_id).order_by(TestCase.id).all()
    if not test_cases:
        return {'error': 'No test cases found for this task'}

    results = []
    tests_passed = 0
    total_execution_time = 0.0
    max_memory_used = 0

    for test_case in test_cases:
        result = run_code(
            code,
            test_case.input_data,
            task.time_limit,
            language
        )

        exec_time = float(result.get('time') or 0)
        mem_used = int(result.get('memory') or 0)

        total_execution_time += exec_time
        max_memory_used = max(max_memory_used, mem_used)

        test_result = {
            'test_id': test_case.id,
            'status': result.get('status', 'system_error'),
            'passed': False,
            'execution_time': exec_time,
            'memory_used': mem_used,
            'error': (result.get('error') or '')[:200]
        }

        if result.get('success'):
            normalized_output = normalize_output(result.get('output', ''))
            normalized_expected = normalize_output(test_case.expected_output)

            if normalized_output == normalized_expected:
                test_result['passed'] = True
                test_result['status'] = 'passed'
                tests_passed += 1
            else:
                test_result['status'] = 'wrong_answer'

        results.append(test_result)

    total_tests = len(test_cases)
    pass_ratio = (tests_passed / total_tests) if total_tests else 0.0
    avg_execution_time = (total_execution_time / total_tests) if total_tests else 0.0

    if tests_passed == total_tests:
        overall_status = 'accepted'
    elif tests_passed > 0:
        overall_status = 'partially_correct'
    elif any(r['status'] == 'time_limit' for r in results):
        overall_status = 'time_limit'
    elif any(r['status'] == 'compilation_error' for r in results):
        overall_status = 'compilation_error'
    elif any(r['status'] == 'runtime_error' for r in results):
        overall_status = 'runtime_error'
    else:
        overall_status = 'wrong_answer'

    return {
        'status': overall_status,
        'tests_passed': tests_passed,
        'total_tests': total_tests,
        'pass_ratio': pass_ratio,
        'execution_time': avg_execution_time,
        'memory_used': max_memory_used,
        'results': results
    }

def get_status_message(status):
    messages = {
        'accepted': 'Решение принято!',
        'partially_correct': 'Частично верно',
        'wrong_answer': 'Неверный ответ',
        'time_limit': 'Превышено ограничение по времени',
        'runtime_error': 'Ошибка выполнения',
        'compilation_error': 'Ошибка компиляции',
        'testing': 'Решение проверяется...'
    }
    return messages.get(status, 'Неизвестный статус')


def calculate_elo_rating(rating1, rating2, result1):
    K = 32  # Коэффициент изменения рейтинга

    expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))

    # Новые рейтинги
    new_rating1 = rating1 + K * (result1 - expected1)
    new_rating2 = rating2 + K * ((1 - result1) - expected2)

    return round(new_rating1), round(new_rating2)


#cd путь/к/твоему/проекту
 МАРШРУТЫ

@app.route('/')
def main():
    return render_template('main.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.is_online = True
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('main_reg'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
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
        return redirect(url_for('login'))
    return render_template('reg.html', form=form)


@app.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    current_user.last_seen = datetime.now(timezone.utc)

    # Отменяем поиск матча при выходе
    matchmaking_system.cancel_search(current_user.id)

    db.session.commit()
    logout_user()
    return redirect(url_for('main'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.elo > current_user.best_elo:
        current_user.best_elo = current_user.elo
        db.session.commit()

    user_attempts = Attempt.query.filter_by(user_id=current_user.id).all()
    total_attempts = len(user_attempts)
    successful_attempts = len([a for a in user_attempts if a.status == 'accepted'])

    solved_tasks_single = db.session.query(func.count(func.distinct(Attempt.task_id))) \
        .outerjoin(MatchResult, MatchResult.attempt_id == Attempt.id) \
        .filter(
            Attempt.user_id == current_user.id,
            Attempt.status == 'accepted',
            MatchResult.id == None
        ).scalar() or 0

    matches = Match.query.filter(
        or_(
            Match.user_id == current_user.id,
            Match.opponent_id == current_user.id
        ),
        Match.result != None
    ).order_by(Match.created_at.desc()).limit(10).all()

    match_history = []
    for match in matches:
        is_user = match.user_id == current_user.id
        opponent_id = match.opponent_id if is_user else match.user_id
        opponent = db.session.get(User, opponent_id)

        match_history.append({
            'opponent': opponent.username,
            'result': match.result if is_user else (
                'win' if match.result == 'loss' else 'loss' if match.result == 'win' else 'draw'
            ),
            'rating_change': match.user_rating_change if is_user else match.opponent_rating_change,
            'date': match.created_at.strftime('%d.%m.%Y %H:%M')
        })

    return render_template(
        'profile.html',
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        match_history=match_history,
        solved_tasks_single=solved_tasks_single
    )


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/tasks')
@login_required
def tasks():
    all_tasks = Task.query.all()
    attempts = Attempt.query.filter_by(user_id=current_user.id).all()
    status_priority = {
        "accepted": 6,
        "partially_correct": 5,
        "wrong_answer": 4,
        "time_limit": 3,
        "runtime_error": 2,
        "compilation_error": 1,
        "testing": 0,
    }
    best_by_task = {}
    for a in attempts:
        task_id = a.task_id
        cur = best_by_task.get(task_id)
        score = a.score or 0
        pr = status_priority.get(a.status, 0)
        exec_time = a.execution_time if a.execution_time is not None else 10**9
        submitted = a.submitted_at or datetime.min.replace(tzinfo=timezone.utc)
        key = (score, pr, -exec_time, submitted.timestamp())
        if cur is None:
            best_by_task[task_id] = {"status": a.status, "key": key}
        else:
            if key > cur["key"]:
                best_by_task[task_id] = {"status": a.status, "key": key}
    best_status_by_task = {tid: v["status"] for tid, v in best_by_task.items()}
    status_label = {
        "accepted": "Полное решение",
        "partially_correct": "Частично верно",
        "wrong_answer": "Неверно",
        "time_limit": "TL",
        "runtime_error": "RE",
        "compilation_error": "CE",
        "testing": "Проверка",
    }

    return render_template(
        'tasks.html',
        tasks=all_tasks,
        best_status_by_task=best_status_by_task,
        status_label=status_label
    )


@app.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)

    active_ttl = datetime.now(timezone.utc) - timedelta(minutes=10)

    active_match = Match.query.filter(
        Match.task_id == task_id,
        or_(
            Match.user_id == current_user.id,
            Match.opponent_id == current_user.id
        ),
        Match.result == None,
        Match.created_at >= active_ttl
    ).order_by(Match.created_at.desc()).first()

    opponent = None
    if active_match:
        opponent_id = active_match.opponent_id if current_user.id == active_match.user_id else active_match.user_id
        opponent = db.session.get(User, opponent_id)

    return render_template('arena.html', task=task, active_match=active_match, opponent=opponent)


@app.route('/main')
def main_page():
    return render_template('main_reg.html')


@app.route('/about_reg')
def about_reg():
    return render_template('about_reg.html')


@app.route('/main_reg')
def main_reg():
    return redirect(url_for('main_page'))


@app.route('/liderboard')
def liderboard():
    leaders = User.query.order_by(desc(User.elo)).limit(50).all()
    for rank, user in enumerate(leaders, 1):
        user.rank = rank
    return render_template('liderboard.html', leaders=leaders, current_user=current_user)


@app.route('/api/leaderboard')
def api_leaderboard():
    leaders = User.query.order_by(desc(User.elo)).limit(50).all()
    leaderboard_data = []
    for rank, user in enumerate(leaders, 1):
        leaderboard_data.append({
            'id': user.id,
            'username': user.username,
            'elo': user.elo,
            'rank': rank,
            'is_current_user': current_user.is_authenticated and user.id == current_user.id
        })
    return jsonify({'leaders': leaderboard_data})


@app.route('/update_elo/<int:user_id>/<int:new_elo>')
@login_required
def update_elo(user_id, new_elo):
    user = db.session.get(User, user_id)
    if user:
        user.elo = new_elo
        if new_elo > user.best_elo:
            user.best_elo = new_elo
        db.session.commit()
        return jsonify({'success': True, 'new_elo': user.elo})
    return jsonify({'success': False})


@app.route('/api/tasks/<int:task_id>/attempts')
@login_required
def get_task_attempts(task_id):
    try:
        attempts = Attempt.query.filter_by(
            user_id=current_user.id,
            task_id=task_id
        ).order_by(Attempt.submitted_at.desc()).limit(50).all()

        attempts_data = []
        for attempt in attempts:
            data = {
                'id': attempt.id,
                'user_id': attempt.user_id,
                'task_id': attempt.task_id,
                'code': attempt.code[:100] + '...' if len(attempt.code) > 100 else attempt.code,
                'language': attempt.language,
                'status': attempt.status,
                'execution_time': round(attempt.execution_time, 3) if attempt.execution_time else None,
                'memory_used': attempt.memory_used,
                'tests_passed': attempt.tests_passed,
                'total_tests': attempt.total_tests,
                'score': attempt.score,
                'error_message': attempt.error_message,
                'submitted_at': attempt.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.submitted_at else None
            }
            attempts_data.append(data)

        return jsonify(attempts_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/solutions/submit', methods=['POST'])
@login_required
def submit_solution():
    try:
        data = request.get_json() or {}

        task_id = data.get('task_id')
        code = data.get('code')
        language = (data.get('language') or 'python')
        match_id = data.get('match_id')

        if not task_id or not code:
            return jsonify({'error': 'Missing task_id or code'}), 400

        task = db.session.get(Task, int(task_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # ===== Дуэль: проверки доступа =====
        match = None
        if match_id:
            match = db.session.get(Match, int(match_id))
            if not match:
                return jsonify({'error': 'Match not found'}), 404

            if current_user.id not in [match.user_id, match.opponent_id]:
                return jsonify({'error': 'Not a participant in this match'}), 403

            if match.result is not None:
                return jsonify({'error': 'Match already finished'}), 400

            if not match.started_at:
                match.started_at = datetime.now(timezone.utc)
                db.session.commit()

        # ===== 1) создаём Attempt (черновик) =====
        attempt = Attempt(
            user_id=current_user.id,
            task_id=task.id,
            code=code,
            language=language,
            status='testing',
            submitted_at=datetime.now(timezone.utc),
            tests_passed=0,
            total_tests=0,
            score=0
        )
        db.session.add(attempt)
        db.session.commit()

        # ===== 2) прогоняем тесты =====
        validation = validate_solution(task.id, code, language)

        tests_passed = int(validation.get('tests_passed') or 0)
        total_tests = int(validation.get('total_tests') or 0)
        avg_execution_time = float(validation.get('execution_time') or 0.0)

        # ===== 3) first_try: это первая попытка по задаче =====
        # attempt уже создан, поэтому <= 1 означает "первая"
        attempts_count = Attempt.query.filter_by(
            user_id=current_user.id,
            task_id=task.id
        ).count()
        is_first_try = (attempts_count <= 1)

        # ===== 4) считаем очки (твоя схема: base + бонусы, округление вверх) =====
        score_info = calculate_task_score(
            task_points=int(task.points or 0),
            tests_passed=tests_passed,
            total_tests=total_tests,
            is_first_try=is_first_try,
            avg_execution_time=avg_execution_time,
            time_limit=int(task.time_limit or 1),
        )

        # ===== 5) заполняем Attempt =====
        attempt.status = validation.get('status', 'error')
        attempt.tests_passed = tests_passed
        attempt.total_tests = total_tests
        attempt.execution_time = avg_execution_time
        attempt.score = int(score_info.get("total") or 0)

        # первая ошибка
        first_error = ""
        for r in (validation.get("results") or []):
            if r.get("error"):
                first_error = r["error"]
                break
        attempt.error_message = (first_error or "")[:1000]

        # ===== одиночный режим =====
        if not match_id:
            db.session.commit()
            return jsonify({
                'attempt_id': attempt.id,
                'status': attempt.status,
                'score': attempt.score,
                'max_score': int(task.points or 0),
                'tests_passed': attempt.tests_passed,
                'total_tests': attempt.total_tests,
                'execution_time': round(attempt.execution_time, 3) if attempt.execution_time else 0,
                'message': get_status_message(attempt.status)
            })

        # ===== дуэль: сохраняем MatchResult =====
        match_result = MatchResult.query.filter_by(
            match_id=match.id,
            user_id=current_user.id
        ).first()

        if match_result:
            match_result.attempt_id = attempt.id
            match_result.score = attempt.score or 0
            match_result.tests_passed = attempt.tests_passed or 0
            match_result.total_tests = attempt.total_tests or 0
            match_result.execution_time = attempt.execution_time
            match_result.submitted_at = datetime.now(timezone.utc)
        else:
            match_result = MatchResult(
                match_id=match.id,
                user_id=current_user.id,
                attempt_id=attempt.id,
                score=attempt.score or 0,
                tests_passed=attempt.tests_passed or 0,
                total_tests=attempt.total_tests or 0,
                execution_time=attempt.execution_time,
                submitted_at=datetime.now(timezone.utc)
            )
            db.session.add(match_result)

        db.session.commit()

        # финализируем матч (ты уже делаешь)
        finalize_match_if_needed(match)

        return jsonify({
            'attempt_id': attempt.id,
            'status': attempt.status,
            'score': attempt.score,
            'max_score': int(task.points or 0),
            'tests_passed': attempt.tests_passed,
            'total_tests': attempt.total_tests,
            'execution_time': round(attempt.execution_time, 3) if attempt.execution_time else 0,
            'message': get_status_message(attempt.status),
            'match_id': match.id,
            'match_status': match.result if match.result else 'in_progress'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/run', methods=['POST'])
@login_required
def run_code_api():
    try:
        data = request.get_json() or {}
        code = data.get('code')
        input_data = data.get('input_data', '')
        language = data.get('language', 'python')
        time_limit = int(data.get('time_limit', 2))

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        result = run_code(code, input_data, time_limit, language)

        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'error': result['error'],
            'execution_time': result['time'],
            'status': result['status']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/attempts/<int:attempt_id>/result')
@login_required
def get_attempt_result(attempt_id):
    try:
        attempt = Attempt.query.get_or_404(attempt_id)

        if attempt.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        result_data = {
            'id': attempt.id,
            'status': attempt.status,
            'tests_passed': attempt.tests_passed,
            'total_tests': attempt.total_tests,
            'score': attempt.score,
            'execution_time': attempt.execution_time,
            'error_message': attempt.error_message,
            'submitted_at': attempt.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.submitted_at else None
        }

        return jsonify(result_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>/sample_test')
@login_required
def get_sample_test(task_id):
    try:
        test_cases = TestCase.query.filter_by(task_id=task_id, is_hidden=False).all()

        sample_tests = []
        for tc in test_cases:
            sample_tests.append({
                'input': tc.input_data,
                'expected_output': tc.expected_output
            })

        return jsonify({'sample_tests': sample_tests})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    try:
        try:
            db.session.execute("SELECT 1")
            db_status = 'connected'
        except Exception:
            db_status = 'disconnected'

        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ================ МАТЧМЕЙКИНГ МАРШРУТЫ ================

@app.route('/matchmaking')
@login_required
def matchmaking_page():
    """Страница поиска матча"""
    return render_template('matchmaking.html')


@app.route('/api/matchmaking/start', methods=['POST'])
@login_required
def start_matchmaking():
    """Начать поиск противника"""
    try:
        data = request.get_json() or {}
        difficulty = data.get('difficulty', 'any')

        # Лог, чтобы быстро отлавливать ситуацию, когда два клиента по ошибке шлют одну и ту же сессию/cookie
        print(f"/api/matchmaking/start -> current_user={current_user.id} ({current_user.username}), ELO={current_user.elo}, difficulty={difficulty}")

        # Проверяем, нет ли уже активного матча.
        # Важно: если сервер был выключен, матч мог "зависнуть" незавершённым.
        # get_active_match_for_user() попробует финализировать такой матч по таймеру.
        active_match = get_active_match_for_user(current_user.id)

        if active_match:
            opponent_id = active_match.opponent_id if current_user.id == active_match.user_id else active_match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, active_match.task_id)

            return jsonify({
                'success': True,
                'match_found': True,
                'match_id': active_match.id,
                'opponent': {
                    'id': opponent.id,
                    'username': opponent.username,
                    'elo': opponent.elo
                },
                'task_id': active_match.task_id,
                'task_title': task.title if task else 'Unknown Task',
                'difficulty': difficulty,
                'message': 'У вас уже есть активный матч'
            })

        # Начинаем поиск (find_opponent сам добавит в очередь или создаст матч)
        result = matchmaking_system.find_opponent(
            user_id=current_user.id,
            user_elo=current_user.elo,
            difficulty=difficulty
        )

        # гарантируем флаги
        if result.get('match_id'):
            result['match_found'] = True
        else:
            result['match_found'] = False

        return jsonify(result)

    except Exception as e:
        print(f"Ошибка при старте матчмейкинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/matchmaking/cancel', methods=['POST'])
@login_required
def cancel_matchmaking():
    try:
        matchmaking_system.cancel_search(current_user.id)
        match = Match.query.filter(
            or_(
                Match.user_id == current_user.id,
                Match.opponent_id == current_user.id
            ),
            Match.result == None
        ).order_by(Match.created_at.desc()).first()
        if match:
            MatchResult.query.filter_by(match_id=match.id).delete()
            db.session.delete(match)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Поиск отменен'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/matchmaking/status', methods=['GET'])
@login_required
def get_matchmaking_status():
    """Получить статус поиска"""
    try:
        # Проверяем, в очереди ли пользователь
        in_queue = MatchmakingQueue.query.filter_by(
            user_id=current_user.id,
            status='searching'
        ).first() is not None

        # Получаем статистику очереди
        queue_stats = matchmaking_system.get_queue_stats(current_user.id) if in_queue else {}

        # Проверяем, найден ли матч (с учётом истечения таймера, если сервер был выключен)
        match = get_active_match_for_user(current_user.id)

        response_data = {
            'in_queue': in_queue,
            'queue_stats': queue_stats,
            'match_found': match is not None
        }

        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)

            response_data.update({
                'match_id': match.id,
                'opponent': {
                    'id': opponent.id,
                    'username': opponent.username,
                    'elo': opponent.elo
                },
                'task_id': match.task_id,
                'task_title': task.title if task else 'Unknown Task'
            })

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/matchmaking/poll', methods=['GET'])
@login_required
def poll_matchmaking():
    """Проверить, найден ли соперник"""
    try:
        # Проверяем, в очереди ли пользователь ПРЯМО СЕЙЧАС (чтобы не "врать" UI)
        in_queue = MatchmakingQueue.query.filter_by(
            user_id=current_user.id,
            status='searching'
        ).first() is not None

        # Обновляем ping пользователя (если он в очереди)
        ping_ok = matchmaking_system.ping_queue(current_user.id) if in_queue else False

        # Проверяем, найден ли матч.
        # Важно: created_at в БД может быть timestamp без timezone (naive).
        # Фильтр по "последним N минутам" с timezone-aware datetime может приводить
        # к тому, что матч не находится у ожидающего игрока. Берём самый свежий матч
        # без жёсткого фильтра по времени.
        match = get_active_match_for_user(current_user.id)

        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)

            return jsonify({
                'match_found': True,
                'match_id': match.id,
                'opponent': {
                    'id': opponent.id,
                    'username': opponent.username,
                    'elo': opponent.elo
                },
                'task_id': match.task_id,
                'task_title': task.title if task else 'Unknown Task'
            })

        # Если матча нет, но пользователя уже нет в очереди — значит поиск истёк/был сброшен.
        queue_stats = matchmaking_system.get_queue_stats(current_user.id) if in_queue else {'total_players': 0}

        return jsonify({
            'match_found': False,
            'still_searching': bool(in_queue),
            'in_queue': bool(in_queue),
            'ping_ok': bool(ping_ok),
            'queue_stats': queue_stats,
            'message': 'Ожидание соперника...' if in_queue else 'Вы не в очереди. Нажмите Start для нового поиска.'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/matchmaking/ping', methods=['POST'])
@login_required
def ping_matchmaking():
    """Обновить активность в очереди"""
    try:
        success = matchmaking_system.ping_queue(current_user.id)

        if success:
            return jsonify({'success': True, 'message': 'Ping updated'})
        else:
            return jsonify({'success': False, 'error': 'Not in queue'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/match/<int:match_id>/status')
@login_required
def get_match_status(match_id):
    """Получить статус матча"""
    try:
        match = Match.query.get_or_404(match_id)

        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403

        finalize_match_if_needed(match)
        db.session.refresh(match)
        user_result = MatchResult.query.filter_by(match_id=match_id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=match.opponent_id).first()

        user_info = db.session.get(User, match.user_id)
        opponent_info = db.session.get(User, match.opponent_id)

        # Результат матча в БД хранится относительно match.user_id (s1):
        #   win  -> победил match.user_id
        #   lose -> победил match.opponent_id
        #   draw -> ничья
        # Для UI удобнее сразу отдать "результат для текущего пользователя".
        is_user_side = (current_user.id == match.user_id)

        result_for_user = match.result
        if match.result in ['win', 'loss'] and not is_user_side:
            result_for_user = 'win' if match.result == 'loss' else 'loss'

        rating_change_for_user = match.user_rating_change if is_user_side else match.opponent_rating_change
        rating_change_for_opponent = match.opponent_rating_change if is_user_side else match.user_rating_change

        # Баллы и тесты тоже отдаём относительно текущего пользователя (чтобы сразу показать всплывашку)
        user_score_for_user = user_result.score if user_result else 0
        opp_score_for_user = opponent_result.score if opponent_result else 0
        user_tests_passed_for_user = user_result.tests_passed if user_result else 0
        user_total_tests_for_user = user_result.total_tests if user_result else 0
        opp_tests_passed_for_user = opponent_result.tests_passed if opponent_result else 0
        opp_total_tests_for_user = opponent_result.total_tests if opponent_result else 0
        if not is_user_side:
            user_score_for_user, opp_score_for_user = opp_score_for_user, user_score_for_user
            user_tests_passed_for_user, opp_tests_passed_for_user = opp_tests_passed_for_user, user_tests_passed_for_user
            user_total_tests_for_user, opp_total_tests_for_user = opp_total_tests_for_user, user_total_tests_for_user

        response_data = {
            'match_id': match.id,
            'result': match.result,
            'result_for_user': result_for_user,
            'task_id': match.task_id,
            'created_at': match.created_at.isoformat() if match.created_at else None,
            'user_rating_change': match.user_rating_change,
            'opponent_rating_change': match.opponent_rating_change,
            'rating_change_for_user': rating_change_for_user,
            'rating_change_for_opponent': rating_change_for_opponent,
            'score_for_user': user_score_for_user,
            'score_for_opponent': opp_score_for_user,
            'tests_passed_for_user': user_tests_passed_for_user,
            'total_tests_for_user': user_total_tests_for_user,
            'tests_passed_for_opponent': opp_tests_passed_for_user,
            'total_tests_for_opponent': opp_total_tests_for_user,
            'participants': {
                'user': {
                    'id': user_info.id,
                    'username': user_info.username,
                    'elo': user_info.elo,
                    'has_submitted': user_result is not None,
                    'score': user_result.score if user_result else 0,
                    'tests_passed': user_result.tests_passed if user_result else 0,
                    'total_tests': user_result.total_tests if user_result else 0,
                },
                'opponent': {
                    'id': opponent_info.id,
                    'username': opponent_info.username,
                    'elo': opponent_info.elo,
                    'has_submitted': opponent_result is not None,
                    'score': opponent_result.score if opponent_result else 0,
                    'tests_passed': opponent_result.tests_passed if opponent_result else 0,
                    'total_tests': opponent_result.total_tests if opponent_result else 0,
                }
            }
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/match/<int:match_id>/opponent_info')
@login_required
def get_opponent_info(match_id):
    """Вернуть данные о сопернике для блока на арене.

    На фронте (templates/arena.html) блок соперника обновляется
    запросом /api/match/<id>/opponent_info. В исходной версии этот
    эндпоинт отсутствовал, из-за чего блок оставался пустым.
    """
    try:
        match = Match.query.get_or_404(match_id)

        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403

        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent_user = db.session.get(User, opponent_id)
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=opponent_id).first()

        return jsonify({
            'id': opponent_user.id,
            'username': opponent_user.username,
            'elo': opponent_user.elo,
            # Пока соперник не отправил решение, результата нет — возвращаем 0.
            'has_submitted': opponent_result is not None,
            'score': (opponent_result.score if opponent_result else 0) or 0,
            'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
            'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
            'execution_time': opponent_result.execution_time if opponent_result else None,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/match/active')
@login_required
def get_active_match():
    """Получить активный матч пользователя"""
    try:
        active_ttl = datetime.now(timezone.utc) - timedelta(minutes=10)

        match = Match.query.filter(
            or_(
                Match.user_id == current_user.id,
                Match.opponent_id == current_user.id
            ),
            Match.result == None,
            Match.created_at >= active_ttl
        ).order_by(Match.created_at.desc()).first()

        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)

            return jsonify({
                'match_id': match.id,
                'opponent': {
                    'id': opponent.id,
                    'username': opponent.username,
                    'elo': opponent.elo
                },
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'difficulty': task.difficulty
                } if task else None
            })

        return jsonify({'match_id': None})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/match/forfeit', methods=['POST'])
@login_required
def forfeit_active_match():
    """Сдаться в активном матче.

    Матч завершается сразу:
    - если сдаётся match.user_id => result = 'loss'
    - если сдаётся opponent_id   => result = 'win'
    """
    try:
        match = get_active_match_for_user(current_user.id)
        if not match:
            return jsonify({'error': 'No active match'}), 400

        # Гарантируем корректное started_at для длительности
        match.started_at = normalize_match_started_at(match)

        # Кто сдаётся и кто побеждает
        forfeiter_id = current_user.id
        if forfeiter_id == match.user_id:
            winner_id = match.opponent_id
            db_result = 'loss'   # относительно match.user_id
        else:
            winner_id = match.user_id
            db_result = 'win'    # относительно match.user_id

        # Если соперник сдаётся, победителю должны начислиться "полные" баллы/тесты.
        # В БД MatchResult требует attempt_id, поэтому создаём технические Attempt/MatchResult.
        task_max = get_task_max_score(match.task_id)
        total_tests = TestCase.query.filter_by(task_id=match.task_id).count()

        def _ensure_forfeit_result(user_id: int, score: int, tests_passed: int, total: int):
            existing = MatchResult.query.filter_by(match_id=match.id, user_id=user_id).first()
            if existing:
                # Не затираем реальный сабмит игрока
                return
            now_ts = datetime.now(timezone.utc)
            attempt = Attempt(
                user_id=user_id,
                task_id=match.task_id,
                code='',
                language='forfeit',
                status='FORFEIT_WIN' if user_id == winner_id else 'FORFEIT_LOSS',
                execution_time=0.0,
                memory_used=0,
                tests_passed=tests_passed,
                total_tests=total,
                score=score,
                error_message=None,
                submitted_at=now_ts,
            )
            db.session.add(attempt)
            db.session.flush()  # получить attempt.id

            mr = MatchResult(
                match_id=match.id,
                user_id=user_id,
                attempt_id=attempt.id,
                score=score,
                tests_passed=tests_passed,
                total_tests=total,
                execution_time=0.0,
                submitted_at=now_ts,
            )
            db.session.add(mr)

        # Победителю — максимум, проигравшему — 0 (если у него не было сабмита)
        _ensure_forfeit_result(winner_id, task_max, total_tests, total_tests)
        _ensure_forfeit_result(forfeiter_id, 0, 0, total_tests)
        db.session.commit()

        _apply_match_result(match, db_result)

        # Вернём данные как в /api/match/<id>/status, чтобы фронт мог показать всплывашку.
        db.session.refresh(match)

        user_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.opponent_id).first()

        is_user_side = (current_user.id == match.user_id)

        result_for_user = match.result
        if match.result in ['win', 'loss'] and not is_user_side:
            result_for_user = 'win' if match.result == 'loss' else 'loss'

        rating_change_for_user = match.user_rating_change if is_user_side else match.opponent_rating_change
        # В UI больше не показываем изменение рейтинга соперника
        rating_change_for_opponent = 0

        user_score_for_user = user_result.score if user_result else 0
        opp_score_for_user = opponent_result.score if opponent_result else 0
        user_tests_passed_for_user = user_result.tests_passed if user_result else 0
        user_total_tests_for_user = user_result.total_tests if user_result else 0
        opp_tests_passed_for_user = opponent_result.tests_passed if opponent_result else 0
        opp_total_tests_for_user = opponent_result.total_tests if opponent_result else 0
        if not is_user_side:
            user_score_for_user, opp_score_for_user = opp_score_for_user, user_score_for_user
            user_tests_passed_for_user, opp_tests_passed_for_user = opp_tests_passed_for_user, user_tests_passed_for_user
            user_total_tests_for_user, opp_total_tests_for_user = opp_total_tests_for_user, user_total_tests_for_user

        return jsonify({
            'ok': True,
            'match_id': match.id,
            'result': match.result,
            'result_for_user': result_for_user,
            'task_id': match.task_id,
            'rating_change_for_user': rating_change_for_user,
            'rating_change_for_opponent': rating_change_for_opponent,
            'score_for_user': user_score_for_user,
            'score_for_opponent': opp_score_for_user,
            'tests_passed_for_user': user_tests_passed_for_user,
            'total_tests_for_user': user_total_tests_for_user,
            'tests_passed_for_opponent': opp_tests_passed_for_user,
            'total_tests_for_opponent': opp_total_tests_for_user,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/match/history')
@login_required
def get_match_history():
    """Получить историю матчей пользователя"""
    try:
        matches = Match.query.filter(
            or_(
                Match.user_id == current_user.id,
                Match.opponent_id == current_user.id
            ),
            Match.result != None
        ).order_by(Match.created_at.desc()).limit(20).all()

        match_history = []
        for match in matches:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)

            # Определяем результат для текущего пользователя
            user_result = 'win' if (current_user.id == match.user_id and match.result == 'win') or \
                                   (current_user.id == match.opponent_id and match.result == 'loss') else \
                'loss' if (current_user.id == match.user_id and match.result == 'loss') or \
                          (current_user.id == match.opponent_id and match.result == 'win') else \
                    'draw'

            rating_change = match.user_rating_change if current_user.id == match.user_id else match.opponent_rating_change

            match_history.append({
                'match_id': match.id,
                'task_id': match.task_id,
                'task_title': task.title if task else 'Unknown',
                'opponent_username': opponent.username,
                'opponent_elo': opponent.elo,
                'result': user_result,
                'rating_change': rating_change,
                'created_at': match.created_at.strftime('%Y-%m-%d %H:%M') if match.created_at else None
            })

        return jsonify({'matches': match_history})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/current')
@login_required
def get_current_user_info():
    """Получить информацию о текущем пользователе"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'elo': current_user.elo,
        'wins': current_user.wins,
        'losses': current_user.losses,
        'draws': current_user.draws,
        'games_played': current_user.games_played,
        'title': current_user.title,
        'best_elo': current_user.best_elo
    })


@app.route('/api/tasks/random')
@login_required
def get_random_task():
    """Получить случайную задачу по сложности"""
    try:
        difficulty = request.args.get('difficulty', 'medium')

        if difficulty == 'any':
            task = Task.query.order_by(db.func.random()).first()
        else:
            task = Task.query.filter_by(difficulty=difficulty).order_by(db.func.random()).first()

        if task:
            return jsonify({
                'id': task.id,
                'title': task.title,
                'difficulty': task.difficulty,
                'points': task.points
            })
        else:
            # Если нет задач нужной сложности, берем любую
            task = Task.query.order_by(db.func.random()).first()
            if task:
                return jsonify({
                    'id': task.id,
                    'title': task.title,
                    'difficulty': task.difficulty,
                    'points': task.points
                })

        return jsonify({'error': 'No tasks available'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/online_players')
@login_required
def get_online_players():
    """Получить статистику онлайн игроков (без имен)"""
    try:
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

        total_online = User.query.filter(
            or_(
                User.is_online == True,
                User.last_seen >= five_minutes_ago
            )
        ).count()

        # Количество игроков в очереди
        total_in_queue = MatchmakingQueue.query.filter(
            MatchmakingQueue.status == 'searching'
        ).join(User, MatchmakingQueue.user_id == User.id).filter(
            or_(User.is_online == True, User.last_seen >= five_minutes_ago)  # Активные пользователи
        ).count()

        return jsonify({
            'total_online': total_online,
            'total_in_queue': total_in_queue
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================ НОВЫЙ МАРШРУТ ДЛЯ ДУЭЛИ ================

@app.route('/duel/<int:match_id>')
@login_required
def duel_arena(match_id):
    """Страница дуэли/соревнования"""
    try:
        # Получаем информацию о матче
        match = Match.query.get_or_404(match_id)

        # Проверяем, является ли пользователь участником матча
        if current_user.id not in [match.user_id, match.opponent_id]:
            return redirect(url_for('matchmaking_page'))

        # Если сервер был выключен, матч мог истечь по времени, но остаться "активным" в БД.
        # Попробуем финализировать его прежде, чем показывать арену.
        finalize_match_if_needed(match)
        db.session.refresh(match)
        if match.result is not None:
            # Матч уже завершён (например, по таймеру). Возвращаем на матчмейкинг.
            return redirect(url_for('matchmaking_page'))

        # Получаем информацию об оппоненте
        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent = db.session.get(User, opponent_id)

        # Получаем информацию о задаче
        task = Task.query.get_or_404(match.task_id)

        # Нормализуем/восстанавливаем время начала матча (в БД может быть naive datetime)
        if not match.started_at:
            match.started_at = to_utc_aware(match.created_at) or datetime.now(timezone.utc)
            db.session.commit()
        else:
            fixed = to_utc_aware(match.started_at)
            if fixed != match.started_at:
                match.started_at = fixed
                db.session.commit()

        # Рассчитываем оставшееся время (2 часа = 7200 секунд)
        match_duration = 7200  # 2 часа в секундах
        started_at = to_utc_aware(match.started_at)
        now_utc = datetime.now(timezone.utc)
        elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
        time_remaining = max(0, match_duration - elapsed_time)

        return render_template('arena.html',
                               task=task,
                               opponent=opponent,
                               current_user=current_user,
                               match=match,
                               time_remaining=time_remaining)

    except Exception as e:
        print(f"Ошибка при загрузке страницы дуэли: {e}")
        return redirect(url_for('matchmaking_page'))


@app.route('/api/duel/<int:match_id>/status')
@login_required
def get_duel_status(match_id):
    try:
        match = Match.query.get_or_404(match_id)

        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403

        # ✅ ВАЖНО: пытаемся завершить матч по времени/макс-скор
        finalize_match_if_needed(match)

        # Рефреш (после finalize match мог измениться)
        db.session.refresh(match)

        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent_user = db.session.get(User, opponent_id)

        user_result = MatchResult.query.filter_by(match_id=match_id, user_id=current_user.id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=opponent_id).first()

        response_data = {
            'match_id': match.id,
            'result': match.result,
            'time_remaining': None,
            'user_rating_change': match.user_rating_change if current_user.id == match.user_id else match.opponent_rating_change,
            'opponent_rating_change': match.opponent_rating_change if current_user.id == match.user_id else match.user_rating_change,
            'participants': {
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'elo': current_user.elo,
                    'has_submitted': user_result is not None,
                    'score': (user_result.score if user_result else 0) or 0,
                    'tests_passed': (user_result.tests_passed if user_result else 0) or 0,
                    'total_tests': (user_result.total_tests if user_result else 0) or 0,
                },
                'opponent': {
                    'id': opponent_user.id,
                    'username': opponent_user.username,
                    'elo': opponent_user.elo,
                    'has_submitted': opponent_result is not None,
                    'score': (opponent_result.score if opponent_result else 0) or 0,
                    'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
                    'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
                }
            }
        }

        # Таймер показываем только если матч не завершен
        if match.result is None and match.started_at:
            started_at = to_utc_aware(match.started_at)
            now_utc = datetime.now(timezone.utc)
            elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
            time_remaining = max(0, duel_max_time - elapsed_time)
            response_data['time_remaining'] = time_remaining
        else:
            response_data['time_remaining'] = 0

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Фоновая задача для обновления статуса онлайн
def update_online_status():
    """Обновление статуса онлайн пользователей"""
    while True:
        try:
            with app.app_context():
                # Помечаем как офлайн пользователей, которые не активны более 5 минут
                five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

                User.query.filter(
                    User.is_online == True,
                    User.last_seen < five_minutes_ago
                ).update({'is_online': False})

                db.session.commit()
        except Exception as e:
            print(f"Ошибка при обновлении статуса онлайн: {e}")

        time.sleep(60)  # Проверяем каждую минуту

@app.before_request
def update_last_seen():
    """Heartbeat пользователя.

    Раньше мы обновляли только last_seen, из-за чего фоновый поток мог выставить
    is_online=False (после 5 минут тишины), и пользователь оставался "офлайн"
    даже при активной работе — это ломало матчмейкинг и статистику очереди.

    Теперь на любой активности мы:
    - обновляем last_seen (не чаще, чем раз в 15 секунд)
    - поднимаем is_online=True
    """
    if not current_user.is_authenticated:
        return

    now = datetime.now(timezone.utc)

    # Если поле last_seen пустое/наивное — приводим к корректному значению
    last_seen = current_user.last_seen
    if last_seen is None or last_seen.tzinfo is None:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()
        return

    # Обновляем не чаще, чем раз в 15 секунд
    if (now - last_seen).total_seconds() >= 15:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()


def calculate_task_score(
    task_points: int,
    tests_passed: int,
    total_tests: int,
    *,
    is_first_try: bool,
    avg_execution_time: float,
    time_limit: int,
) -> dict:
    task_points = int(task_points or 0)
    total_tests = int(total_tests or 0)
    tests_passed = int(tests_passed or 0)

    if task_points <= 0 or total_tests <= 0:
        return {"base": 0, "bonus": 0, "total": 0}

    tests_passed = max(0, min(tests_passed, total_tests))
    # 1) base score (базовое кол-во очков за задачу)
    progress = tests_passed / total_tests
    base_score = math.ceil(task_points * progress)
    if tests_passed == 0:
        base_score = 0
    # 2) max bonus (максимальный бонус за задачу)
    max_bonus = math.ceil(task_points * 0.25)
    bonus = 0
    # 3) accept с первой попытки (10% от task.points)
    if is_first_try and tests_passed > 0:
        bonus += math.ceil(task_points * 0.10)
    # 4) бонус за быстроту выполнения кода (8% от task.points)
    if tests_passed > 0 and avg_execution_time is not None and time_limit:
        tl = max(1, int(time_limit))
        ratio = avg_execution_time / tl
        # задаём метрику:
        #<=0.30 => максимальный бонус 8%
        #<=0.60 => бонус в размере 4%
        #<=0.90 => бонус в размере 2%
        #>0.90  => нету бонуса
        if ratio <= 0.30:
            speed_factor = 1.0
        elif ratio <= 0.60:
            speed_factor = 0.5
        elif ratio <= 0.90:
            speed_factor = 0.2
        else:
            speed_factor = 0.0

        bonus += math.ceil(task_points * 0.08 * speed_factor)

    bonus = min(bonus, max_bonus)
    total = base_score + bonus
    # Не даём выходить за пределы шкалы задачи (иначе получается 22/20 и т.п.)
    total = min(int(total), int(task_points))

    # ВАЖНО для дуэлей: "полный балл" должен означать 100% тестов,
    # а не ситуацию, когда частичное решение добирает очки бонусами.
    # Иначе матч может завершиться досрочно на частично верном решении.
    if total_tests > 0 and tests_passed < total_tests and task_points > 0:
        total = min(total, max(0, int(task_points) - 1))

    return {
        "base": int(base_score),
        "bonus": int(bonus),
        "total": int(total)
    }

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        online_status_thread = threading.Thread(target=update_online_status, daemon=True)
        online_status_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
