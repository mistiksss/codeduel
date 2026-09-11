"""Flask extensions instantiated without an application.

Call ``init_app`` from the application factory. Keeping a single module
avoids circular imports between models, routes and services.
"""

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
