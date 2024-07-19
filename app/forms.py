from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo,  ValidationError
from app.models import User, Car
import re



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
class RegistrationForm(FlaskForm):
    username = StringField('Име', validators=[DataRequired(), Length(min=2, max=20)])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30)])
    password = PasswordField('Парола', validators=[DataRequired()])
    confirm_password = PasswordField('Повтори паролата', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Регистрация')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Този номер е зает опитайте с друг')


class LoginForm(FlaskForm):
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30)])
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
    additional_info = TextAreaField('Информация за автомобила', validators=[DataRequired()])
    submit = SubmitField('Запази промените')


class CreateVisitForm(FlaskForm):
    description = TextAreaField('Информация за ремонта', validators=[DataRequired()])
    submit = SubmitField('Запази')



class AdminCreateUserForm(FlaskForm):
    username = StringField('Име', validators=[DataRequired(), Length(min=2, max=20)])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=30)])
    password = PasswordField('Парола', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвърди паролата', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Роля', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Запази')

class AdminEditUserForm(FlaskForm):
    username = StringField('Име', validators=[DataRequired(), Length(min=2, max=20)])
    phone_number = StringField('Телефонен номер', validators=[DataRequired(), Length(min=10, max=15)])
    role = SelectField('Роля', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Запази')

    def __init__(self, original_username=None, original_phone_number=None, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_phone_number = original_phone_number

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Името е заето, моля изберете друго')

    def validate_phone_number(self, phone_number):
        if phone_number.data != self.original_phone_number:
            user = User.query.filter_by(phone_number=phone_number.data).first()
            if user:
                raise ValidationError('Вече съществува потребител с този телефонен номер')