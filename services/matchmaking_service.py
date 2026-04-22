from datetime import datetime, timezone, timedelta
import threading

from sqlalchemy import or_

from extensions import db
from models import User, Task, Match, MatchmakingQueue


class MatchmakingSystem:
    def __init__(self):
        self.search_lock = threading.Lock()
        self.ELO_RANGE = 300
        self.MAX_SEARCH_TIME = 300

    def _find_opponent_in_queue(self, user_id, user_elo, difficulty, difficulty_filter=None, use_elo_range=True):
        online_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        online_filter = or_(User.is_online == True, User.last_seen >= online_cutoff)

        base_filter = [
            MatchmakingQueue.user_id != user_id,
            MatchmakingQueue.status == 'searching',
            online_filter,
        ]
        if difficulty_filter:
            base_filter.append(MatchmakingQueue.difficulty == difficulty_filter)
        if use_elo_range:
            base_filter.append(MatchmakingQueue.elo.between(user_elo - self.ELO_RANGE, user_elo + self.ELO_RANGE))

        query = MatchmakingQueue.query.filter(*base_filter).join(
            User, MatchmakingQueue.user_id == User.id
        )
        if use_elo_range:
            query = query.order_by(db.func.abs(MatchmakingQueue.elo - user_elo), MatchmakingQueue.joined_at)
        else:
            query = query.order_by(MatchmakingQueue.joined_at)

        return query.first()

    def find_opponent(self, user_id, user_elo, difficulty=None):
        with self.search_lock:
            try:
                print(f"Поиск противника для пользователя {user_id} (ELO: {user_elo})")
                self._cleanup_old_entries()

                search_params = []
                if difficulty and difficulty != 'any':
                    search_params.append((difficulty, True))
                search_params.append((None, True))
                search_params.append((None, False))

                for diff_filter, use_elo in search_params:
                    opponent = self._find_opponent_in_queue(
                        user_id, user_elo, difficulty,
                        difficulty_filter=diff_filter,
                        use_elo_range=use_elo
                    )
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
            existing = MatchmakingQueue.query.filter_by(user_id=user_id, status='searching').first()
            if existing:
                existing.last_ping = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'success': True,
                    'in_queue': True,
                    'queue_id': existing.id,
                    'message': 'Вы уже в очереди поиска'
                }

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
            deleted = MatchmakingQueue.query.filter_by(user_id=user_id, status='searching').delete()
            return deleted > 0

    def ping_queue(self, user_id):
        try:
            updated = MatchmakingQueue.query.filter_by(
                user_id=user_id, status='searching'
            ).update({'last_ping': datetime.now(timezone.utc)})
            db.session.commit()
            return updated > 0
        except Exception as e:
            db.session.rollback()
            return False

    def get_queue_stats(self, user_id):
        try:
            five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            total_in_queue = MatchmakingQueue.query.filter_by(status='searching').join(
                User, MatchmakingQueue.user_id == User.id
            ).filter(or_(User.is_online == True, User.last_seen >= five_minutes_ago)).count()
            return {'total_players': total_in_queue}
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {'total_players': 0}