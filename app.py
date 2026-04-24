import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
from markupsafe import Markup
from sqlalchemy import desc, or_, func, text
from datetime import datetime, timezone, timedelta
from executor import run_code
import bleach
import os
import time
import threading
import traceback

from extensions import db

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'postgresql://postgres:54321@localhost:5432/code_duel'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-change-in-production'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['CODE_EXECUTION_TIMEOUT'] = 5
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

db.init_app(app)

from models import User, Task, TestCase, Attempt, Match, MatchResult, MatchmakingQueue
from flask_socketio import SocketIO
bcrypt = Bcrypt(app)
app.bcrypt = bcrypt

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
app.socketio = socketio

from sockets import register_socket_handlers
register_socket_handlers(socketio)

# Import services AFTER app and db are initialized to avoid circular import issues
from services.match_service import (
    to_utc_aware,
    normalize_match_started_at,
    _apply_match_result,
    _build_match_response_for_user,
    get_active_match_for_user,
    get_task_max_score,
    finalize_match_if_needed,
    DUEL_MAX_TIME as duel_max_time,
)
from services.matchmaking_service import MatchmakingSystem
from services.scoring import validate_solution, calculate_task_score

if LIMITER_AVAILABLE:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=os.environ.get('REDIS_URL') or 'memory://',
        default_limits=[],
        strategy='fixed-window',
    )
else:
    limiter = None

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def _get_active_page():
    ep = request.endpoint if request else None
    if ep in ('main', 'main_page', 'main_reg'):
        return 'main'
    if ep == 'tasks':
        return 'tasks'
    if ep in ('profile', 'user_public_profile'):
        return 'profile'
    if ep == 'leaderboard':
        return 'leaderboard'
    if ep in ('about', 'about_reg'):
        return 'about'
    if ep == 'match.matchmaking_page':
        return 'main'
    if ep == 'match.duel_arena':
        return 'tasks'
    return None


@app.context_processor
def inject_active_match_to_templates():
    ctx = {'active_page': _get_active_page()}
    try:
        if current_user.is_authenticated:
            m = get_active_match_for_user(current_user.id)
            badges = _user_badges(current_user)
            ctx.update({
                'active_match': m,
                'active_match_id': (m.id if m else None),
                'user_badges': badges,
            })
    except Exception as e:
        app.logger.warning("inject_active_match failed: %s", e)
    if 'active_match' not in ctx:
        ctx.update({'active_match': None, 'active_match_id': None, 'user_badges': []})
    return ctx


matchmaking_system = MatchmakingSystem()

ALLOWED_HTML_TAGS = {'p', 'br', 'code', 'pre', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'span', 'div'}


def safe_html(text):
    if text is None:
        return Markup('')
    s = str(text).strip()
    if not s:
        return Markup('')
    cleaned = bleach.clean(s, tags=ALLOWED_HTML_TAGS, strip=True)
    return Markup(cleaned)


app.jinja_env.filters['safe_html'] = safe_html


def get_status_message(status):
    messages = {
        'accepted': 'Решение принято!',
        'partially_correct': 'Частично верно',
        'wrong_answer': 'Неверный ответ',
        'time_limit': 'Превышено ограничение по времени',
        'runtime_error': 'Ошибка выполнения',
        'compilation_error': 'Ошибка компиляции',
        'testing': 'Решение проверяется...',
    }
    return messages.get(status, 'Неизвестный статус')


@app.route('/')
def main():
    return render_template('main.html')


from routes.auth import auth_bp
from routes.match import match_bp

app.register_blueprint(auth_bp)
app.register_blueprint(match_bp)
app.matchmaking_system = matchmaking_system

if limiter:
    from routes.auth import login as auth_login_view
    app.view_functions['auth.login'] = limiter.limit("5 per minute")(auth_login_view)


@app.errorhandler(429)
def too_many_requests(e):
    return render_template('error_429.html'), 429


def _user_badges(user):
    badges = []
    wins = getattr(user, 'wins', 0) or 0
    streak = getattr(user, 'current_streak', 0) or 0
    if wins >= 1:
        badges.append(('Первая кровь', '1 победа'))
    if streak > 3:
        badges.append(('В огне', f'серия {streak} побед'))
    return badges


def _profile_context(profile_user, match_limit=5):
    user_attempts = Attempt.query.filter_by(user_id=profile_user.id).all()
    total_attempts = len(user_attempts)
    successful_attempts = len([a for a in user_attempts if a.status == 'accepted'])

    solved_tasks_single = db.session.query(func.count(func.distinct(Attempt.task_id))) \
        .outerjoin(MatchResult, MatchResult.attempt_id == Attempt.id) \
        .filter(
            Attempt.user_id == profile_user.id,
            Attempt.status == 'accepted',
            MatchResult.id == None
        ).scalar() or 0

    matches = Match.query.filter(
        or_(
            Match.user_id == profile_user.id,
            Match.opponent_id == profile_user.id
        ),
        Match.result != None
    ).order_by(Match.created_at.desc()).limit(match_limit).all()

    opponent_ids = list({m.opponent_id if m.user_id == profile_user.id else m.user_id for m in matches})
    opponents_by_id = {}
    if opponent_ids:
        opponents_by_id = {u.id: u for u in User.query.filter(User.id.in_(opponent_ids)).all()}

    match_history = []
    for match in matches:
        is_user_side = match.user_id == profile_user.id
        opponent_id = match.opponent_id if is_user_side else match.user_id
        opponent = opponents_by_id.get(opponent_id)
        match_history.append({
            'opponent': opponent.username if opponent else '—',
            'result': match.result if is_user_side else (
                'win' if match.result == 'loss' else 'loss' if match.result == 'win' else 'draw'
            ),
            'rating_change': match.user_rating_change if is_user_side else match.opponent_rating_change,
            'date': match.created_at.strftime('%d.%m.%Y %H:%M') if match.created_at else ''
        })

    rank = User.query.filter(User.elo > profile_user.elo).count() + 1
    wins = getattr(profile_user, 'wins', 0) or 0
    losses = getattr(profile_user, 'losses', 0) or 0
    winrate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
    current_streak = getattr(profile_user, 'current_streak', 0) or 0

    return {
        'profile_user': profile_user,
        'total_attempts': total_attempts,
        'successful_attempts': successful_attempts,
        'match_history': match_history,
        'solved_tasks_single': solved_tasks_single,
        'badges': _user_badges(profile_user),
        'rank': rank,
        'winrate': winrate,
        'current_streak': current_streak,
    }


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.elo > current_user.best_elo:
        current_user.best_elo = current_user.elo
        db.session.commit()

    ctx = _profile_context(current_user, match_limit=3)
    ctx['is_own_profile'] = True
    return render_template('profile.html', **ctx)


@app.route('/user/<username>')
def user_public_profile(username):
    profile_user = User.query.filter_by(username=username).first_or_404()
    ctx = _profile_context(profile_user, match_limit=3)
    ctx['is_own_profile'] = current_user.is_authenticated and current_user.id == profile_user.id
    return render_template('profile.html', **ctx)


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

    return render_template('arena.html', task=task, match=active_match, active_match=active_match, opponent=opponent)


@app.route('/main')
def main_page():
    return render_template('main_reg.html')


@app.route('/about_reg')
def about_reg():
    return render_template('about_reg.html')


@app.route('/main_reg')
def main_reg():
    return redirect(url_for('main_page'))


@app.route('/leaderboard')
def leaderboard():
    leaders = User.query.order_by(desc(User.elo)).limit(50).all()
    for rank, user in enumerate(leaders, 1):
        user.rank = rank
    return render_template('leaderboard.html', leaders=leaders, current_user=current_user)


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
            'is_current_user': current_user.is_authenticated and user.id == current_user.id,
        })
    return jsonify({'leaders': leaderboard_data})


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
@(limiter.limit("10 per minute") if limiter else lambda f: f)
@login_required
def submit_solution():
    try:
        data = request.get_json() or {}

        task_id = data.get('task_id')
        code = data.get('code')
        language = (data.get('language') or 'python').strip().lower()
        match_id = data.get('match_id')

        if not task_id or not code:
            return jsonify({'error': 'Missing task_id or code'}), 400

        if language != 'python':
            return jsonify({'error': 'Only Python is supported'}), 400

        MAX_CODE_LENGTH = 10 * 1024
        if len(code) > MAX_CODE_LENGTH:
            return jsonify({'error': f'Code exceeds maximum length ({MAX_CODE_LENGTH} characters)'}), 400

        task = db.session.get(Task, int(task_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404

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

        if match_id:
            try:
                socketio.emit('opponent_testing', {}, room=str(match_id))
            except Exception as e:
                app.logger.warning("socketio opponent_testing emit failed: %s", e)

        validation = validate_solution(task.id, code, language)

        tests_passed = int(validation.get('tests_passed') or 0)
        total_tests = int(validation.get('total_tests') or 0)
        avg_execution_time = float(validation.get('execution_time') or 0.0)

        attempts_count = Attempt.query.filter_by(
            user_id=current_user.id,
            task_id=task.id
        ).count()
        is_first_try = (attempts_count <= 1)
        score_info = calculate_task_score(
            task_points=int(task.points or 0),
            tests_passed=tests_passed,
            total_tests=total_tests,
            is_first_try=is_first_try,
            avg_execution_time=avg_execution_time,
            time_limit=int(task.time_limit or 1),
        )

        attempt.status = validation.get('status', 'error')
        attempt.tests_passed = tests_passed
        attempt.total_tests = total_tests
        attempt.execution_time = avg_execution_time
        attempt.score = int(score_info.get("total") or 0)
        attempt.error_message = _extract_first_error(validation)[:1000]

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

        _upsert_match_result(match, current_user.id, attempt)
        db.session.commit()
        finalize_match_if_needed(match)
        db.session.refresh(match)

        try:
            match_data = _get_match_broadcast_data(match)
            match_data['is_finished'] = match.result is not None
            socketio.emit('match_update', match_data, room=str(match.id))
            if match.result:
                socketio.emit('match_finished', match_data, room=str(match.id))
        except Exception as e:
            app.logger.error(f"CRITICAL SOCKET ERROR: {e}")

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
            db.session.execute(text("SELECT 1"))
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

def update_online_status():
    while True:
        try:
            with app.app_context():
                five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

                User.query.filter(
                    User.is_online == True,
                    User.last_seen < five_minutes_ago
                ).update({'is_online': False})

                db.session.commit()
        except Exception as e:
            print(f"Ошибка при обновлении статуса онлайн: {e}")

        time.sleep(60)

@app.before_request
def update_last_seen():
    if not current_user.is_authenticated:
        return

    now = datetime.now(timezone.utc)

    last_seen = current_user.last_seen
    if last_seen is None or last_seen.tzinfo is None:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()
        return

    if (now - last_seen).total_seconds() >= 15:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()


def _get_match_broadcast_data(match) -> dict:
    return {'match_id': match.id}


def _extract_first_error(validation: dict) -> str:
    for result in (validation.get("results") or []):
        if result.get("error"):
            return str(result["error"])
    return ""


def _upsert_match_result(match, user_id: int, attempt) -> None:
    match_result = MatchResult.query.filter_by(match_id=match.id, user_id=user_id).first()
    now_utc = datetime.now(timezone.utc)
    if match_result:
        match_result.attempt_id = attempt.id
        match_result.score = attempt.score or 0
        match_result.tests_passed = attempt.tests_passed or 0
        match_result.total_tests = attempt.total_tests or 0
        match_result.execution_time = attempt.execution_time
        match_result.submitted_at = now_utc
    else:
        match_result = MatchResult(
            match_id=match.id,
            user_id=user_id,
            attempt_id=attempt.id,
            score=attempt.score or 0,
            tests_passed=attempt.tests_passed or 0,
            total_tests=attempt.total_tests or 0,
            execution_time=attempt.execution_time,
            submitted_at=now_utc,
        )
        db.session.add(match_result)


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        online_status_thread = threading.Thread(target=update_online_status, daemon=True)
        online_status_thread.start()
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, allow_unsafe_werkzeug=True)
