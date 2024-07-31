from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app, bcrypt, db
from app.forms import   MechanicProfileForm, AdminCreateUserForm, AdminEditUserForm, UpdateAccountForm, EditCarForm 
from app.models import User, Car, Role, RepairShopImage
from flask_paginate import Pagination, get_page_args
import os
import secrets
from PIL import Image
from flask import current_app, session


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
        app.logger.info('Form validated successfully')
        try:
            # Check if the phone number is already registered
            user = User.query.filter_by(phone_number=form.phone_number.data).first()
            if user:
                flash(f'Потребител с телефонен номер: {form.phone_number.data} е вече регистриран.', 'danger')
                return redirect(url_for('create_user'))

            # Hash the password
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            # Create a new user
            user = User(username=form.username.data, email=form.email.data, phone_number=form.phone_number.data, password=hashed_password)
            db.session.add(user)
            db.session.flush()

            # Assign role to the new user
            role = Role.query.get(form.role.data)
            if role:
                user.roles.append(role)
            
            db.session.commit()
            flash(f'User {form.username.data} регистриран успешно!', 'success')
            app.logger.info(f'{current_user.username} created user {user.phone_number}')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating user: {str(e)}')
            flash('Възникна грешка при създаването на потребителя. Моля, опитайте отново.', 'danger')
    
    if form.errors:
        app.logger.info(f'Form errors: {form.errors}')
    
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
        user.biography = form.biography.data
        user.expertise = form.expertise.data

        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data, folder='profile_pics')
            user.image_file = picture_file

        if form.repair_shop_pictures.data:
            for picture in request.files.getlist(form.repair_shop_pictures.name):
                picture_file = save_picture(picture, folder='repair_shop_pics')
                repair_shop_image = RepairShopImage(image_file=picture_file, user_id=user.id)
                db.session.add(repair_shop_image)

        user.roles = []
        new_role = Role.query.get(form.role.data)
        if new_role:
            user.roles.append(new_role)

        db.session.commit()
        app.logger.info(f'{current_user.username} updated user {user.phone_number}')
        flash(f'User {user.username} редактиран успешно!', 'success')
        return redirect(url_for('admin_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.phone_number.data = user.phone_number
        form.biography.data = user.biography
        form.expertise.data = user.expertise
        form.role.data = user.roles[0].id if user.roles else ''
    
    repair_shop_images = RepairShopImage.query.filter_by(user_id=user.id).all()
    return render_template('admin/edit_user.html', form=form, user=user, repair_shop_images=repair_shop_images)



@app.route("/delete_user/<int:user_id>", methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)

    if user.is_mechanic():
        # Get another mechanic to reassign the cars
        new_mechanic = User.query.filter(User.roles.any(Role.name == 'mechanic'), User.id != user_id).first()
        if not new_mechanic:
            flash('No other mechanic found to reassign cars. Please create another mechanic first.', 'danger')
            return redirect(url_for('admin_users'))

        # Reassign all cars to the new mechanic
        cars = Car.query.filter_by(mechanic_id=user.id).all()
        for car in cars:
            car.mechanic_id = new_mechanic.id
        db.session.commit()
        flash(f'All cars have been reassigned to mechanic {new_mechanic.username}.', 'info')

    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been successfully deleted!', 'success')
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
    nonce = os.urandom(16).hex()
    session['nonce'] = nonce
    return google.authorize_redirect(redirect_uri, nonce=nonce)

def generate_unique_username(base_username):
    count = 1
    new_username = base_username
    while User.query.filter_by(username=new_username).first():
        new_username = f"{base_username}{count}"
        count += 1
    return new_username


@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    nonce = session.pop('nonce', None)
    if not nonce:
        flash('Nonce not found in session.', 'danger')
        return redirect(url_for('login'))

    user_info = google.parse_id_token(token, nonce=nonce)
    
    if user_info:
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            unique_username = generate_unique_username(user_info['name'])
            user = User(
                username=unique_username,
                email=user_info['email'],
                phone_number='0000000000',  # Temporary default phone number
                password=os.urandom(12).hex()  # Default random password
            )
            db.session.add(user)
            db.session.flush()  # Flush to get the user ID

            # Assign the default role
            default_role = Role.query.filter_by(name='frontend_user').first()
            if default_role:
                user.roles.append(default_role)
            db.session.commit()
        
        login_user(user)
        if user.phone_number == '0000000000':
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


@app.route('/admin_cars', methods=['GET', 'POST'])
@login_required
def admin_cars():
    form = EditCarForm()
    form.mechanic_id.choices = [(mechanic.id, mechanic.username) for mechanic in User.query.filter(User.roles.any(Role.name == 'mechanic')).all()]

    visibility = request.args.get('visibility')
    if visibility:
        cars = Car.query.filter_by(visibility=(visibility == 'true')).all()
    else:
        cars = Car.query.all()

    # Implement pagination if necessary
    pagination = None  # Replace with actual pagination if used

    return render_template('admin/admin_cars.html', cars=cars, pagination=pagination, form=form)

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

@app.route('/delete_repair_shop_image_admin/<int:image_id>', methods=['POST'])
@login_required
def delete_repair_shop_image_admin(image_id):
    if not current_user.is_admin():
        flash('You do not have permission to delete this image.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    image = RepairShopImage.query.get_or_404(image_id)
    
    # Delete the image file from the filesystem
    picture_path = os.path.join(current_app.root_path, 'static/repair_shop_pics', image.image_file)
    if os.path.exists(picture_path):
        os.remove(picture_path)

    db.session.delete(image)
    db.session.commit()
    flash('Image has been deleted!', 'success')
    return redirect(url_for('edit_user', user_id=image.user_id))

@app.route('/admin_update_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def admin_update_car(car_id):
    car = Car.query.get_or_404(car_id)
    form = EditCarForm()
    form.mechanic_id.choices = [(mechanic.id, mechanic.username) for mechanic in User.query.filter(User.roles.any(Role.name == 'mechanic')).all()]
    
    if form.validate_on_submit():
        car.registration_number = form.registration_number.data
        car.vin_number = form.vin_number.data
        car.additional_info = form.additional_info.data
        car.owner.name = form.owner_name.data
        car.owner.phone_number = form.owner_phone_number.data
        car.mechanic_id = form.mechanic_id.data
        db.session.commit()
        flash('Car and owner details updated successfully!', 'success')
        return redirect(url_for('admin_cars'))
    elif request.method == 'GET':
        form.registration_number.data = car.registration_number
        form.vin_number.data = car.vin_number
        form.additional_info.data = car.additional_info
        form.owner_name.data = car.owner.name
        form.owner_phone_number.data = car.owner.phone_number
        form.mechanic_id.data = car.mechanic_id
    
    return render_template('admin/admin_cars.html', form=form, car=car)
