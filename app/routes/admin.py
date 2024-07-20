from app import app, bcrypt, db
from flask import render_template, url_for, flash, redirect, request
from app.forms import RegistrationForm, LoginForm, CreateCarForm, AdminCreateUserForm, AdminEditUserForm, UpdateAccountForm
from app.models import User, Car, Role
from flask_login import login_user, current_user, logout_user, login_required
from flask_paginate import Pagination, get_page_args
import os
import secrets
from PIL import Image
from flask import current_app

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn



@app.route("/create_user", methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))

    form = AdminCreateUserForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        user = User.query.filter_by(phone_number=form.phone_number.data).first()
        if user:
            flash(f'Потребител с телефонен номер:  {form.phone_number.data} е вече регистриран.', 'danger')
            return redirect(url_for('create_user'))

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, phone_number=form.phone_number.data, password=hashed_password)
        db.session.add(user)
        db.session.flush()
        

        role = Role.query.get(form.role.data)
        if role:
            user.roles.append(role)
        
        db.session.commit()
        flash(f'User {form.username.data} регистриран успешно!', 'success')
        app.logger.info(f'{current_user.username}  created user {user.phone_number}')
        return redirect(url_for('admin_users'))
        

    return render_template('admin/create_user.html', form=form)

@app.route("/search_users", methods=['GET'])
@login_required
def search_users():
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))
    
    query = request.args.get('query')
    if query:
        users = User.query.filter(User.username.contains(query) | User.phone_number.contains(query)).all()
    else:
        users = User.query.all()

    form = AdminCreateUserForm()
    return render_template('admin/admin_users.html', form=form, users=users)

@app.route("/edit_user/<int:user_id>", methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    form = AdminEditUserForm(original_username=user.username, original_phone_number=user.phone_number)
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.phone_number = form.phone_number.data

        user.roles = []
        new_role = Role.query.get(form.role.data)
        if new_role:
            user.roles.append(new_role)

        db.session.commit()
        app.logger.info(f'{current_user.username}  updated user {user.phone_number}')
        flash(f'User {user.username} редактиран успешно!', 'success')
        return redirect(url_for('admin_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.phone_number.data = user.phone_number
        form.role.data = user.roles[0].id if user.roles else ''
    
    return render_template('admin/edit_user.html', form=form, user=user)

@app.route("/delete_user/<int:user_id>", methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    user.visibility = False
    db.session.commit()
    flash(f'User {user.username} е изтрит успешно!', 'success')
    app.logger.info(f'{current_user.username}  deleted user {user.phone_number}')
    return redirect(url_for('admin_users'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, phone_number=form.phone_number.data, password=hashed_password)
        
        role = Role.query.filter_by(name='frontend_user').first()
        if role:
            if role not in user.roles:
                user.roles.append(role)  
            db.session.add(user)
            db.session.commit()
        
        flash(f'Регистрацията успешна за {form.username.data}!', 'success')
        app.logger.info(f'New user registered with {user.phone_number}')
        return redirect(url_for('login'))
        
    return render_template('admin/register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phone_number=form.phone_number.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            app.logger.info(f'{current_user.username}  logged with {user.phone_number}')
            return redirect(next_page) if next_page else redirect(url_for('home'))

        else:
            flash('Грешен Телефонен номер или парола', 'danger')

    return render_template('admin/login.html', title='Login', form=form)

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/admin_dashboard.html')

@app.route('/admin_users', methods=['GET'])
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('home'))

    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=10)
    query = request.args.get('query')

    if query:
        users_query = User.query.filter(User.username.contains(query) | User.phone_number.contains(query))
    else:
        users_query = User.query

    total = users_query.count()
    users = users_query.offset(offset).limit(per_page).all()

    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('admin/admin_users.html', users=users, pagination=pagination)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    user = User.query.get_or_404(current_user.id)
    form = UpdateAccountForm()

    if form.validate_on_submit():
        user.username = form.username.data
        user.phone_number = form.phone_number.data
        if form.picture.data:
            picture_file = save_picture(form.picture.data)  # Implement the save_picture function to handle file saving
            user.image_file = picture_file
        if form.password.data:  # Only update password if it is provided
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = user.username
        form.phone_number.data = user.phone_number

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('admin/account.html', title='Account', form=form, image_file=image_file)





@app.route("/restore_car_visibility/<int:car_id>", methods=["POST"])
@login_required
def restore_car_visibility(car_id):
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))

    car = Car.query.get_or_404(car_id)
    car.visibility = True
    db.session.commit()
    flash(f'Car {car.registration_number} visibility restored successfully!', 'success')
    return redirect(url_for('admin_cars'))

@app.route('/admin_cars', methods=['GET'])
@login_required
def admin_cars():
    if not current_user.is_admin():
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('home'))

    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=10)
    visibility_filter = request.args.get('visibility')

    if visibility_filter == 'true':
        cars_query = Car.query.filter_by(visibility=True)
    elif visibility_filter == 'false':
        cars_query = Car.query.filter_by(visibility=False)
    else:
        cars_query = Car.query

    total = cars_query.count()
    cars = cars_query.offset(offset).limit(per_page).all()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('admin/admin_cars.html', cars=cars, pagination=pagination)
