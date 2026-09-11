"""Queue-based opponent search for 1v1 duels."""

import logging
import threading
from datetime import timedelta

from sqlalchemy import or_

from constants import (
    MATCHMAKING_ELO_RANGE,
    MATCHMAKING_MAX_SEARCH_SECONDS,
    ONLINE_TIMEOUT_MINUTES,
)
from extensions import db
from models import Match, MatchmakingQueue, Task, User
from utils.utc import utc_now

logger = logging.getLogger(__name__)


class MatchmakingSystem:
    """Find an opponent, create a Match, or put the player in the queue.

    Search order (unchanged):

    1. Same difficulty + Elo within ``ELO_RANGE``
    2. Any difficulty + Elo within ``ELO_RANGE``
    3. Anyone still searching (oldest first)
    """

    def __init__(self):
        self.search_lock = threading.Lock()
        self.ELO_RANGE = MATCHMAKING_ELO_RANGE
        self.MAX_SEARCH_TIME = MATCHMAKING_MAX_SEARCH_SECONDS

    def _find_opponent_in_queue(
        self,
        user_id,
        user_elo,
        difficulty,
        difficulty_filter=None,
        use_elo_range=True,
    ):
        """Return the best queued opponent matching the given filters."""
        online_cutoff = utc_now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
        online_filter = or_(User.is_online == True, User.last_seen >= online_cutoff)  # noqa: E712

        filters = [
            MatchmakingQueue.user_id != user_id,
            MatchmakingQueue.status == 'searching',
            online_filter,
        ]
        if difficulty_filter:
            filters.append(MatchmakingQueue.difficulty == difficulty_filter)
        if use_elo_range:
            filters.append(
                MatchmakingQueue.elo.between(user_elo - self.ELO_RANGE, user_elo + self.ELO_RANGE),
            )

        query = MatchmakingQueue.query.filter(*filters).join(
            User, MatchmakingQueue.user_id == User.id,
        )
        if use_elo_range:
            query = query.order_by(
                db.func.abs(MatchmakingQueue.elo - user_elo),
                MatchmakingQueue.joined_at,
            )
        else:
            query = query.order_by(MatchmakingQueue.joined_at)

        return query.first()

    def find_opponent(self, user_id, user_elo, difficulty=None):
        """Try to pair ``user_id`` or enqueue them if nobody matches."""
        with self.search_lock:
            try:
                logger.info('Searching opponent for user %s (ELO: %s)', user_id, user_elo)
                self._cleanup_old_entries()

                search_params = []
                if difficulty and difficulty != 'any':
                    search_params.append((difficulty, True))
                search_params.append((None, True))
                search_params.append((None, False))

                for difficulty_filter, use_elo_range in search_params:
                    opponent = self._find_opponent_in_queue(
                        user_id,
                        user_elo,
                        difficulty,
                        difficulty_filter=difficulty_filter,
                        use_elo_range=use_elo_range,
                    )
                    if opponent:
                        logger.info(
                            'Found opponent %s for user %s (difficulty=%s)',
                            opponent.user_id,
                            user_id,
                            difficulty,
                        )
                        return self._create_match(user_id, opponent.user_id, difficulty)

                return self._add_to_queue(user_id, user_elo, difficulty)

            except Exception:
                db.session.rollback()
                logger.exception('Error while searching for an opponent')
                raise

    def _get_random_task_by_difficulty(self, difficulty):
        """Return a random task id for ``difficulty``, or ``None``."""
        try:
            if difficulty == 'any' or not difficulty:
                task = Task.query.order_by(db.func.random()).first()
            else:
                task = Task.query.filter_by(difficulty=difficulty).order_by(db.func.random()).first()
            return task.id if task else None
        except Exception:
            logger.exception('Error while picking a random task')
            return None

    def _create_match(self, user1_id, user2_id, difficulty):
        """Create a Match row and mark both queue entries as matched.

        The lower user id is stored as ``Match.user_id`` so the pair is
        stored in a stable order regardless of who clicked Search first.
        """
        try:
            task_id = self._get_random_task_by_difficulty(difficulty)
            if not task_id:
                task_id = self._get_random_task_by_difficulty('any')
            if not task_id:
                raise Exception('No tasks in database')

            task = db.session.get(Task, task_id)
            if user1_id < user2_id:
                db_user_id, db_opponent_id = user1_id, user2_id
            else:
                db_user_id, db_opponent_id = user2_id, user1_id

            MatchmakingQueue.query.filter(
                MatchmakingQueue.user_id.in_([user1_id, user2_id]),
                MatchmakingQueue.status == 'searching',
            ).update({'status': 'matched'})

            now = utc_now()
            match = Match(
                user_id=db_user_id,
                opponent_id=db_opponent_id,
                task_id=task_id,
                created_at=now,
                started_at=now,
                result=None,
            )
            db.session.add(match)
            db.session.commit()

            logger.info(
                'Created match id=%s task_id=%s users=(%s,%s)',
                match.id,
                task_id,
                db_user_id,
                db_opponent_id,
            )
            opponent_user = db.session.get(User, user2_id)

            return {
                'success': True,
                'match_found': True,
                'match_id': match.id,
                'opponent_id': opponent_user.id,
                'opponent': {
                    'id': opponent_user.id,
                    'username': opponent_user.username,
                    'elo': opponent_user.elo,
                },
                'task_id': task_id,
                'task_title': task.title if task else 'Unknown Task',
                'difficulty': difficulty,
                'message': 'Соперник найден!',
            }
        except Exception:
            db.session.rollback()
            raise

    def _add_to_queue(self, user_id, user_elo, difficulty):
        """Insert a searching queue row, or refresh ping if already queued."""
        try:
            existing = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching',
            ).first()
            if existing:
                existing.last_ping = utc_now()
                db.session.commit()
                return {
                    'success': True,
                    'in_queue': True,
                    'queue_id': existing.id,
                    'message': 'Вы уже в очереди поиска',
                }

            now = utc_now()
            queue_entry = MatchmakingQueue(
                user_id=user_id,
                elo=user_elo,
                task_id=None,
                difficulty=difficulty,
                status='searching',
                joined_at=now,
                last_ping=now,
            )
            db.session.add(queue_entry)
            db.session.commit()
            logger.info('User %s added to matchmaking queue', user_id)
            return {
                'success': True,
                'in_queue': True,
                'queue_id': queue_entry.id,
                'message': 'Ожидание соперника...',
            }
        except Exception:
            db.session.rollback()
            raise

    def _cleanup_old_entries(self):
        """Drop searching rows whose last ping is older than MAX_SEARCH_TIME."""
        stale_before = utc_now() - timedelta(seconds=self.MAX_SEARCH_TIME)
        MatchmakingQueue.query.filter(
            MatchmakingQueue.last_ping < stale_before,
            MatchmakingQueue.status == 'searching',
        ).delete()
        db.session.commit()

    def cancel_search(self, user_id):
        """Remove the user from the searching queue.

        Does not commit — callers that also mutate other rows (logout,
        cancel endpoint) own the transaction.
        """
        with self.search_lock:
            deleted = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching',
            ).delete()
            return deleted > 0

    def ping_queue(self, user_id):
        """Refresh ``last_ping`` so the player is not cleaned out as stale."""
        try:
            updated = MatchmakingQueue.query.filter_by(
                user_id=user_id,
                status='searching',
            ).update({'last_ping': utc_now()})
            db.session.commit()
            return updated > 0
        except Exception:
            db.session.rollback()
            return False

    def get_queue_stats(self, user_id):
        """Return how many online players are currently searching."""
        try:
            five_minutes_ago = utc_now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
            total_in_queue = (
                MatchmakingQueue.query.filter_by(status='searching')
                .join(User, MatchmakingQueue.user_id == User.id)
                .filter(or_(User.is_online == True, User.last_seen >= five_minutes_ago))  # noqa: E712
                .count()
            )
            return {'total_players': total_in_queue}
        except Exception:
            logger.exception('Error while loading queue stats')
            return {'total_players': 0}
