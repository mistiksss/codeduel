"""Create tables and fill an empty database with demo tasks and a guest account."""

from extensions import db
from models import Task, TestCase, User

DEMO_EMAIL = 'demo@example.com'
DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'demo123'

TASKS = [
    {
        'title': 'Сумма двух чисел',
        'description': 'Даны два целых числа. Выведите их сумму.',
        'input_description': 'Два целых числа a и b через пробел.',
        'output_description': 'Одно целое число — сумма a и b.',
        'difficulty': 'easy',
        'points': 20,
        'time_limit': 1,
        'memory_limit': 64,
        'cases': [('2 3', '5', False), ('-5 10', '5', True), ('0 0', '0', True)],
    },
    {
        'title': 'Максимум из двух',
        'description': 'Даны два целых числа. Найдите наибольшее из них.',
        'input_description': 'Два целых числа a и b через пробел.',
        'output_description': 'Максимум из двух чисел.',
        'difficulty': 'easy',
        'points': 20,
        'time_limit': 1,
        'memory_limit': 64,
        'cases': [('8 5', '8', False), ('-3 2', '2', True), ('7 7', '7', True)],
    },
    {
        'title': 'Четное или нечетное',
        'description': 'Дано целое число. Определите, чётное оно или нет.',
        'input_description': 'Одно целое число n.',
        'output_description': 'Строка "четное" или "нечетное".',
        'difficulty': 'easy',
        'points': 20,
        'time_limit': 1,
        'memory_limit': 64,
        'cases': [('6', 'четное', False), ('7', 'нечетное', True), ('0', 'четное', True)],
    },
    {
        'title': 'Сумма цифр числа',
        'description': 'Дано целое число. Найдите сумму его цифр (без учёта знака).',
        'input_description': 'Одно целое число n.',
        'output_description': 'Сумма цифр.',
        'difficulty': 'medium',
        'points': 50,
        'time_limit': 1,
        'memory_limit': 64,
        'cases': [('123', '6', False), ('-456', '15', True), ('0', '0', True)],
    },
    {
        'title': 'Палиндром',
        'description': 'Дана строка. Проверьте, читается ли она одинаково слева направо и справа налево.',
        'input_description': 'Одна строка s.',
        'output_description': '"YES" если палиндром, иначе "NO".',
        'difficulty': 'medium',
        'points': 50,
        'time_limit': 1,
        'memory_limit': 64,
        'cases': [('racecar', 'YES', False), ('hello', 'NO', True), ('a', 'YES', True)],
    },
    {
        'title': 'Простое число',
        'description': 'Определите, является ли число простым.',
        'input_description': 'Одно целое число n (n ≥ 1).',
        'output_description': '"YES" если простое, иначе "NO".',
        'difficulty': 'hard',
        'points': 80,
        'time_limit': 2,
        'memory_limit': 64,
        'cases': [('7', 'YES', False), ('1', 'NO', True), ('10', 'NO', True), ('2', 'YES', True)],
    },
]


def seed_if_empty(app):
    """Skip when tasks already exist. Safe to call on every boot."""
    if Task.query.first() is not None:
        return

    for spec in TASKS:
        payload = dict(spec)
        cases = payload.pop('cases')
        task = Task(**payload)
        db.session.add(task)
        db.session.flush()
        for input_data, expected_output, is_hidden in cases:
            db.session.add(TestCase(
                task_id=task.id,
                input_data=input_data,
                expected_output=expected_output,
                is_hidden=is_hidden,
            ))

    if User.query.filter_by(email=DEMO_EMAIL).first() is None:
        db.session.add(User(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            password_hash=app.bcrypt.generate_password_hash(DEMO_PASSWORD).decode('utf-8'),
            onboarding_completed=True,
        ))

    db.session.commit()
    app.logger.info('Seeded demo tasks and user %s', DEMO_EMAIL)
