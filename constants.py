"""Domain constants shared across routes and services.

These values are part of the product contract (UI labels, match duration,
scoring windows). Changing them changes runtime behaviour.
"""

# Duel / matchmaking
DUEL_MAX_TIME_SECONDS = 7200
ACTIVE_MATCH_TTL_MINUTES = 10
MATCHMAKING_ELO_RANGE = 300
MATCHMAKING_MAX_SEARCH_SECONDS = 300
ELO_K_FACTOR = 32

# Presence
ONLINE_TIMEOUT_MINUTES = 5
LAST_SEEN_UPDATE_SECONDS = 15
PRESENCE_SWEEP_INTERVAL_SECONDS = 60

# Solutions
MAX_CODE_LENGTH_CHARS = 10 * 1024
MAX_OUTPUT_CHARS = 50_000
MAX_ERROR_MESSAGE_LENGTH = 1000
DEFAULT_RUN_TIME_LIMIT_SECONDS = 2
MAX_STDIN_CHARS = 100_000
SANDBOX_MEMORY_BYTES = 512 * 1024 * 1024
SANDBOX_MAX_FILE_BYTES = 8 * 1024 * 1024
SANDBOX_MAX_OPEN_FILES = 64

# Task difficulty: stored as easy/medium/hard, shown in Russian.
DIFFICULTY_LABELS = {
    'easy': 'легкая',
    'medium': 'средняя',
    'hard': 'сложная',
}
LEADERBOARD_SIZE = 50
MAX_ATTEMPTS_RETURNED = 50
PROFILE_MATCH_HISTORY_LIMIT = 3
CODE_PREVIEW_LENGTH = 100

# HTML sanitization for task statements
ALLOWED_HTML_TAGS = {
    'p', 'br', 'code', 'pre', 'strong', 'em', 'b', 'i',
    'ul', 'ol', 'li', 'span', 'div',
}

# Attempt status ranking used to pick a user's best result per task.
# Higher number wins when scores are equal.
ATTEMPT_STATUS_PRIORITY = {
    'accepted': 6,
    'partially_correct': 5,
    'wrong_answer': 4,
    'time_limit': 3,
    'runtime_error': 2,
    'compilation_error': 1,
    'testing': 0,
}

ATTEMPT_STATUS_LABELS = {
    'accepted': 'Полное решение',
    'partially_correct': 'Частично верно',
    'wrong_answer': 'Неверно',
    'time_limit': 'TL',
    'runtime_error': 'RE',
    'compilation_error': 'CE',
    'testing': 'Проверка',
}

ATTEMPT_STATUS_MESSAGES = {
    'accepted': 'Решение принято!',
    'partially_correct': 'Частично верно',
    'wrong_answer': 'Неверный ответ',
    'time_limit': 'Превышено ограничение по времени',
    'runtime_error': 'Ошибка выполнения',
    'compilation_error': 'Ошибка компиляции',
    'testing': 'Решение проверяется...',
}

UNKNOWN_STATUS_MESSAGE = 'Неизвестный статус'

MISSING_EXECUTION_TIME_SENTINEL = 10**9
