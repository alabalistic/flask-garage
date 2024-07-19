from app import app, bcrypt, db
from flask import render_template, url_for, flash, redirect, request
from app.forms import RegistrationForm, LoginForm, CreateCarForm, AdminCreateUserForm, AdminEditUserForm
from app.models import User, Car, Role
from flask_login import login_user, current_user, logout_user, login_required

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

@app.route("/admin_users", methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))
    
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, phone_number=form.phone_number.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        role = Role.query.filter_by(name=form.role.data).first()
        if role:
            user.roles.append(role)
            db.session.commit()
        
        flash(f'User {form.username.data} регистриран успешно', 'success')
        app.logger.info(f'{current_user.username}  updated {user.phone_number}')

        return redirect(url_for('admin_users'))

    users = User.query.filter_by(visibility=True).all()
    return render_template('admin/admin_users.html', form=form, users=users)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')

@app.route("/admin_cars", methods=['GET', 'POST'])
@login_required
def admin_cars():
    if not current_user.is_admin():
        flash('Достъп отказан!', 'danger')
        return redirect(url_for('home'))

    filter_visibility = request.args.get('visibility')

    cars_query = Car.query

    if filter_visibility:
        visibility = filter_visibility.lower() == 'true'
        cars_query = cars_query.filter_by(visibility=visibility)

    cars = cars_query.all()

    return render_template('admin/admin_cars.html', cars=cars)


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
