"""WTForms for auth."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo

from models import User


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    confirm_password = PasswordField(validators=[InputRequired(), EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("Это имя пользователя уже занято. Пожалуйста, выберите другое.")


class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=70)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=30)])
    submit = SubmitField('Войти')
