"""Registration and login forms."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import Email, EqualTo, InputRequired, Length, ValidationError

from models import User


class RegisterForm(FlaskForm):
    """Create a new account. Username uniqueness is checked against the DB."""

    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    confirm_password = PasswordField(
        validators=[InputRequired(), EqualTo('password', message='Пароли не совпадают')],
    )
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        """Reject usernames that are already taken."""
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError(
                'Это имя пользователя уже занято. Пожалуйста, выберите другое.',
            )


class LoginForm(FlaskForm):
    """Authenticate with email and password."""

    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    submit = SubmitField('Войти')
