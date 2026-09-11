"""Map Flask endpoint names to the header's ``active_page`` value."""


def get_active_page(endpoint):
    """Return the header section for ``endpoint``, or ``None``.

    Endpoint names here must stay in sync with route function names:
    page views are registered on the app (not a blueprint) so templates
    can keep using ``url_for('tasks')``, ``url_for('profile')``, etc.
    """
    if endpoint in ('main', 'main_page', 'main_reg'):
        return 'main'
    if endpoint == 'tasks':
        return 'tasks'
    if endpoint in ('profile', 'user_public_profile'):
        return 'profile'
    if endpoint == 'leaderboard':
        return 'leaderboard'
    if endpoint in ('about', 'about_reg'):
        return 'about'
    if endpoint == 'match.matchmaking_page':
        return 'main'
    if endpoint == 'match.duel_arena':
        return 'tasks'
    return None
