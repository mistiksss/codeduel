"""Matchmaking and duel HTTP API (blueprint name ``match``)."""

from routes.match.blueprint import match_bp
from routes.match import duels, matchmaking  # noqa: F401  — register routes on match_bp

__all__ = ['match_bp']
