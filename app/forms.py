from flask_wtf import FlaskForm
from wtforms import StringField, FileField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Email
from flask_wtf.file import FileAllowed
from flask_login import current_user
import re
from app.models import User


def validate_phone_number_format(form, field):
    phone_number = field.data
    # Example validation: Only allow digits and ensure length is between 10 and 30
    if not re.match(r'^\d{10,30}$', phone_number):
        raise ValidationError('Invalid phone number. Only digits are allowed and it must be between 10 and 30 digits long.')

CYRILLIC_TO_LATIN_MAP = {
    'А': 'A', 
    'В': 'B', 
    'Е': 'E',
    'К': 'K', 
    'М': 'M', 
    'Н': 'H', 
    'О': 'O', 
    'Р': 'P', 
    'С': 'C', 
    'Т': 'T', 
    'У': 'Y', 
    'Х': 'X'
}

def validate_registration_number(form, field):
    registration_number = field.data.upper()
    transformed_number = ""
    
    for char in registration_number:
        if char in CYRILLIC_TO_LATIN_MAP:
            transformed_number += CYRILLIC_TO_LATIN_MAP[char]
        elif char.isdigit() or char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            transformed_number += char
        else:
            raise ValidationError('Invalid character in registration number: {}'.format(char))
    
    # Update the field data with the transformed number
    field.data = transformed_number.upper()

class LoginForm(FlaskForm):
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30), validate_phone_number_format])
    password = PasswordField('Парола', validators=[DataRequired()])
    remember = BooleanField('Запомни ме')
    submit = SubmitField('Вход')

class CreateCarForm(FlaskForm):
    registration_number = StringField('Регистрационен номер', validators=[DataRequired(), validate_registration_number])
    vin_number = StringField('VIN номер', validators=[DataRequired()])
    additional_info = TextAreaField('Информация за автомобила')
    owner_name = StringField('Име на собственика', validators=[DataRequired()])
    owner_phone_number = StringField('Телефонен номер на собственика', validators=[DataRequired()])
    submit = SubmitField('Запази колата')

class UpdateCarForm(FlaskForm):
    vin_number = StringField('VIN номер', validators=[DataRequired()])
    additional_info = TextAreaField('Информация за автомобила', validators=[DataRequired()])
    submit = SubmitField('Запази промените')

class CreateVisitForm(FlaskForm):
    description = TextAreaField('Информация за ремонта', validators=[DataRequired()])
    submit = SubmitField('Запази')

class AdminCreateUserForm(FlaskForm):
    username = StringField('Име', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30)])
    password = PasswordField('Парола', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвърди паролата', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Роля', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Запази')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Името е заето, моля изберете друго')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email вече е регистриран, моля изберете друг')

class AdminEditUserForm(FlaskForm):
    username = StringField('Име', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30)])
    biography = TextAreaField('Биография', validators=[Optional(), Length(max=500)])
    expertise = StringField('Експертиза', validators=[Optional(), Length(max=200)])
    profile_picture = FileField('Качи профилна снимка', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    role = SelectField('Роля', coerce=int, validators=[DataRequired()])
    repair_shop_pictures = FileField('Качи снимки на сервиза', validators=[FileAllowed(['jpg', 'jpeg', 'png'])], render_kw={"multiple": True})
    submit = SubmitField('Запази')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Името е заето, моля изберете друго')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email вече е регистриран, моля изберете друг')

class UpdateAccountForm(FlaskForm):
    username = StringField('Потребителско име', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30), validate_phone_number_format])
    picture = FileField('Избери профилна снимка', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    biography = TextAreaField('Биография', validators=[Optional(), Length(max=500)])
    expertise = StringField('Експертиза', validators=[Optional(), Length(max=200)])
    password = PasswordField('Нова парола', validators=[Optional(), Length(min=6, max=60), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Повтори паролата')
    submit = SubmitField('Запази промените')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Името е заето, моля изберете друго')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email вече е регистриран, моля изберете друг')

class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Comment')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class MechanicProfileForm(FlaskForm):
    username = StringField('Потребителско име', validators=[DataRequired(), Length(min=2, max=20)])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30), validate_phone_number_format])
    biography = TextAreaField('Биография', validators=[Optional(), Length(max=500)])
    expertise = StringField('Експертиза', validators=[Optional(), Length(max=200)])
    profile_picture = FileField('Качи профилна снимка', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    repair_shop_pictures = FileField('Качи снимки на сервиза', validators=[FileAllowed(['jpg', 'jpeg', 'png'])], render_kw={"multiple": True})
    submit = SubmitField('Запази промените')

class EditCarForm(FlaskForm):
    registration_number = StringField('Регистрационен номер', validators=[DataRequired(), Length(min=2, max=10)])
    vin_number = StringField('VIN номер', validators=[DataRequired(), Length(min=17, max=17)])
    additional_info = TextAreaField('Информация за автомобила', validators=[DataRequired()])
    owner_name = StringField('Име на собственика', validators=[DataRequired(), Length(min=2, max=100)])
    owner_phone_number = StringField('Телефонен номер на собственика', validators=[DataRequired(), Length(min=10, max=30)])
    mechanic_id = SelectField('Механик', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Запази промените')
