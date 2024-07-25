# mechanic.py
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask_paginate import Pagination, get_page_args
from app import app, db
from app.forms import CreateCarForm, CreateVisitForm, UpdateCarForm
from app.models import Car, CarOwner, CarVisit


@app.route("/create_car", methods=["POST", "GET"])
@login_required
def create_car():
    if not current_user.is_mechanic():
        flash('Достъп отказан. Тук се допускат само механици!', 'danger')
        return redirect(url_for('home'))

    form = CreateCarForm()
    if form.validate_on_submit():
        try:
            owner = CarOwner.query.filter_by(phone_number=form.owner_phone_number.data).first()
            if not owner:
                owner = CarOwner(name=form.owner_name.data, phone_number=form.owner_phone_number.data)
                db.session.add(owner)
                db.session.flush()

            car = Car.query.filter_by(registration_number=form.registration_number.data.upper(), mechanic_id=current_user.id).first()
            if car:
                if car.visibility:
                    flash('This car already exists in your fleet. Redirecting to create a visit.', 'info')
                    return redirect(url_for('create_visit', car_id=car.id))
                else:
                    car.visibility = True
                    car.vin_number = form.vin_number.data.upper()
                    car.additional_info = form.additional_info.data
                    car.owner_id = owner.id
                    db.session.commit()
                    flash('Car restored successfully!', 'success')
                    return redirect(url_for('mechanic_dashboard'))
            else:
                new_car = Car(
                    registration_number=form.registration_number.data.upper(),
                    vin_number=form.vin_number.data.upper(),
                    additional_info=form.additional_info.data,
                    owner_id=owner.id,
                    mechanic_id=current_user.id
                )
                db.session.add(new_car)
                db.session.commit()
                flash('Car added successfully!', 'success')
                return redirect(url_for('mechanic_dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('mechanic/create_car.html', form=form)

@app.route('/car/<int:car_id>', methods=['GET'])
@login_required
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=5)

    search_query = request.args.get('search', '').strip()

    visits_query = CarVisit.query.filter_by(car_id=car_id)

    if search_query:
        visits_query = visits_query.filter(
            (CarVisit.description.ilike(f'%{search_query}%')) |
            (CarVisit.date.like(f'%{search_query}%'))
        )

    total = visits_query.count()
    visits = visits_query.offset(offset).limit(per_page).all()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('mechanic/car_detail.html', car=car, visits=visits, pagination=pagination, search_query=search_query)

@app.route('/mechanic_dashboard', methods=['GET', 'POST'])
@login_required
def mechanic_dashboard():
    search_query = request.args.get('search', '').strip()
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=10)
    mechanic_id = current_user.id

    if search_query:
        cars_query = Car.query.filter(
            (Car.mechanic_id == mechanic_id) &
            (Car.visibility == True) &
            ((Car.registration_number.contains(search_query)) |
             (Car.owner.has(CarOwner.phone_number.contains(search_query))))
        )
    else:
        cars_query = Car.query.filter_by(mechanic_id=mechanic_id, visibility=True)

    total = cars_query.count()
    cars = cars_query.offset(offset).limit(per_page).all()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('mechanic/mechanic_dashboard.html', cars=cars, pagination=pagination)

@app.route("/delete_car/<int:car_id>", methods=["POST"])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.mechanic_id != current_user.id:
        flash('You do not have permission to delete this car.', 'danger')
        return redirect(url_for('mechanic_dashboard'))

    car.visibility = False
    db.session.commit()
    flash('Car deleted successfully!', 'success')
    return redirect(url_for('mechanic_dashboard'))

@app.route("/update_car/<int:car_id>", methods=['GET', 'POST'])
@login_required
def update_car(car_id):
    car = Car.query.get_or_404(car_id)
    form = UpdateCarForm()
    
    if form.validate_on_submit():
        car.vin_number = form.vin_number.data
        car.additional_info = form.additional_info.data
        db.session.commit()
        flash('Car details updated successfully!', 'success')
        app.logger.info(f'{current_user.username} updated car {car.registration_number}')

        return redirect(url_for('mechanic_dashboard'))
    
    elif request.method == 'GET':
        form.vin_number.data = car.vin_number
        form.additional_info.data = car.additional_info
    
    return render_template('mechanic/update_car.html', form=form, car=car)

@app.route("/create_visit/<int:car_id>", methods=["POST", "GET"])
@login_required
def create_visit(car_id):
    car = Car.query.get_or_404(car_id)
    if car.mechanic_id != current_user.id:
        flash('Access denied. You do not have permission to add a visit to this car.', 'danger')
        return redirect(url_for('home'))

    form = CreateVisitForm()
    if form.validate_on_submit():
        visit = CarVisit(date=datetime.utcnow(), description=form.description.data, car_id=car.id)
        db.session.add(visit)
        db.session.commit()
        flash('Visit added successfully!', 'success')
        app.logger.info(f'{current_user.username} created visit for car {car.registration_number}')

        return redirect(url_for('car_detail', car_id=car.id))

    return render_template('mechanic/create_visit.html', form=form, car=car)
