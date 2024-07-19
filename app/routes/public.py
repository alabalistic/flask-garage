from app import app, bcrypt, db
from flask import render_template, url_for, flash, redirect, request
from app.forms import RegistrationForm, LoginForm, CreateCarForm, AdminCreateUserForm, AdminEditUserForm
from app.models import User, Car, Role
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    return render_template('public/home.html', posts=Car.query.all())

@app.route("/about")
def about():
    return render_template('public/about.html', title='About')

@app.route("/garage")
def garage():
    return render_template('mechanic/garage.html', title='Garage', cars=Car.query.all())


