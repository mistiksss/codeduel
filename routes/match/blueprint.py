"""Shared Flask blueprint for matchmaking and duel routes."""

from flask import Blueprint

match_bp = Blueprint('match', __name__, url_prefix='')
