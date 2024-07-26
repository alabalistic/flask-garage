from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app, bcrypt, db
from app.forms import RegistrationForm, LoginForm, MechanicProfileForm, AdminCreateUserForm, AdminEditUserForm, UpdateAccountForm
from app.models import User, Car, Role, RepairShopImage
from flask_paginate import Pagination, get_page_args
import os
import secrets
from PIL import Image
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_picture(form_picture, folder='profile_pics'):
    if not allowed_file(form_picture.filename):
        raise ValueError("Unsupported file type. Please upload a .jpg, .jpeg, or .png file.")

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', folder, picture_fn)

    output_size = (500, 500)
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
        user = User(username=form.username.data, email=form.email.data, phone_number=form.phone_number.data, password=hashed_password)
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
    form = AdminEditUserForm(original_username=user.username, original_email=user.email, original_phone_number=user.phone_number)
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
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
        form.email.data = user.email
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
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} е изтрит успешно!', 'success')
    app.logger.info(f'{current_user.username}  deleted user {user.phone_number}')
    return redirect(url_for('admin_users'))

from app import oauth, google

# @app.route("/register", methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
    
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         user = User(username=form.username.data, email=form.email.data, phone_number=form.phone_number.data, password=hashed_password)
        
#         role = Role.query.filter_by(name='frontend_user').first()
#         if role:
#             if role not in user.roles:
#                 user.roles.append(role)  
#             db.session.add(user)
#             db.session.commit()
        
#         flash(f'Регистрацията успешна за {form.username.data}!', 'success')
#         app.logger.info(f'New user registered with {user.phone_number}')
#         return redirect(url_for('login'))
        
#     return render_template('admin/register.html', title='Register', form=form)


@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token)
    
    if user_info:
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                username=user_info['name'],
                email=user_info['email'],
                phone_number=None,  # Initially set to None
                password=os.urandom(12).hex()  # Default random password
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        if not user.phone_number:
            return redirect(url_for('update_phone_number'))
        return redirect(url_for('home'))
    
    flash('Failed to authenticate with Google.', 'danger')
    return redirect(url_for('login'))

@app.route('/update_phone_number', methods=['GET', 'POST'])
@login_required
def update_phone_number():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        user = current_user
        user.phone_number = phone_number
        db.session.commit()
        flash('Your phone number has been updated!', 'success')
        return redirect(url_for('home'))
    
    return render_template('update_phone_number.html')


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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    user = User.query.get_or_404(current_user.id)
    form = UpdateAccountForm()

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.phone_number = form.phone_number.data
            user.biography = form.biography.data
            user.expertise = form.expertise.data
            if form.picture.data:
                picture_file = save_picture(form.picture.data, folder='profile_pics')
                user.image_file = picture_file
            if form.password.data:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user.password = hashed_password
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('account'))
        except ValueError as e:
            flash(str(e), 'danger')

    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.phone_number.data = user.phone_number
        form.biography.data = user.biography
        form.expertise.data = user.expertise

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

@app.route("/mechanic_profile/update", methods=['GET', 'POST'])
@login_required
def update_mechanic_profile():
    if not current_user.is_mechanic():
        flash('Достъп отказан. Само механици могат да актуализират профила си.', 'danger')
        return redirect(url_for('home'))

    form = MechanicProfileForm()
    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.phone_number = form.phone_number.data
            current_user.biography = form.biography.data
            current_user.expertise = form.expertise.data

            if form.profile_picture.data:
                picture_file = save_picture(form.profile_picture.data, folder='profile_pics')
                current_user.image_file = picture_file

            if form.repair_shop_pictures.data:
                for picture in request.files.getlist(form.repair_shop_pictures.name):
                    picture_file = save_picture(picture, folder='repair_shop_pics')
                    repair_shop_image = RepairShopImage(image_file=picture_file, user_id=current_user.id)
                    db.session.add(repair_shop_image)

            db.session.commit()
            flash('Профилът ви е актуализиран!', 'success')
            return redirect(url_for('mechanic_profile', mechanic_id=current_user.id))
        except ValueError as e:
            flash(str(e), 'danger')

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.phone_number.data = current_user.phone_number
        form.biography.data = current_user.biography
        form.expertise.data = current_user.expertise

    return render_template('public/update_mechanic_profile.html', title='Актуализиране на профила', form=form)
