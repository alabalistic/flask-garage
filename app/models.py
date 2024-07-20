from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visibility = db.Column(db.Boolean, nullable=False, default=True)
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f"User('{self.username}', '{self.phone_number}')"

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def is_admin(self):
        return self.has_role('admin')

    def is_mechanic(self):
        return self.has_role('mechanic')
    def is_car_owner(self):
        return self.has_role('car_owner')

# Association table for user roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Role('{self.name}')"

class CarOwner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    cars = db.relationship('Car', backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"CarOwner('{self.name}', '{self.phone_number}')"

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(10), nullable=False)
    vin_number = db.Column(db.String(17), nullable=False)
    additional_info = db.Column(db.String(), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visibility = db.Column(db.Boolean, nullable=False, default=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('car_owner.id'), nullable=False)
    mechanic_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visits = db.relationship('CarVisit', backref='car', lazy=True, cascade='all, delete-orphan')
    mechanic = db.relationship('User', backref='cars', lazy=True)
    __table_args__ = (db.UniqueConstraint('registration_number', 'mechanic_id', name='_registration_mechanic_uc'),)

    def __repr__(self):
        return f"Car('{self.registration_number}', '{self.vin_number}')"
    
class CarVisit(db.Model):
    __tablename__ = 'car_visit'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(), nullable=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)


    def __repr__(self):
        return f"CarVisit('{self.date}', '{self.description}')"

# Extend AnonymousUserMixin
class Anonymous(AnonymousUserMixin):
    def is_admin(self):
        return False

    def is_mechanic(self):
        return False

    def is_car_owner(self):
        return False

login_manager.anonymous_user = Anonymous


