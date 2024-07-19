from app import app, bcrypt, db
from sqlalchemy.exc import IntegrityError
from flask import render_template, url_for, flash, redirect, request, jsonify
from app.forms import CreateCarForm, CreateVisitForm, UpdateCarForm
from app.models import Car, CarOwner, CarVisit, User
from flask_login import current_user, login_required
from datetime import datetime
from google.cloud import speech
import os

# Initialize the Google Cloud Speech client
client = speech.SpeechClient.from_service_account_file(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))

@app.route("/create_car", methods=["POST", "GET"])
@login_required
def create_car():
    if not current_user.is_mechanic():
        flash('Access denied. Mechanics only!', 'danger')
        return redirect(url_for('home'))

    form = CreateCarForm()
    if form.validate_on_submit():
        try:
            owner = CarOwner.query.filter_by(phone_number=form.owner_phone_number.data).first()
            if not owner:
                owner = CarOwner(name=form.owner_name.data, phone_number=form.owner_phone_number.data)
                db.session.add(owner)
                db.session.flush()

            car = Car(
                registration_number=form.registration_number.data.upper(),
                vin_number=form.vin_number.data.upper(),
                additional_info=form.additional_info.data,
                owner_id=owner.id,
                mechanic_id=current_user.id
            )
            db.session.add(car)
            db.session.commit()
            flash('Car added successfully!', 'success')
            app.logger.info(f'{current_user.username} added car {car.registration_number}')
            return redirect(url_for('mechanic_dashboard'))
        except IntegrityError:
            db.session.rollback()
            existing_car = Car.query.filter_by(registration_number=form.registration_number.data.upper(), mechanic_id=current_user.id).first()
            if existing_car:
                flash('This car already exists in your fleet. Redirecting to create a visit.', 'info')
                return redirect(url_for('create_visit', car_id=existing_car.id))
            else:
                flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('mechanic/create_car.html', form=form)

@app.route("/car/<int:car_id>", methods=['GET'])
@login_required
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    if car.mechanic_id != current_user.id:
        flash('Access denied. You do not have permission to view this car.', 'danger')
        return redirect(url_for('home'))
    
    visits = CarVisit.query.filter_by(car_id=car.id).all()
    return render_template('mechanic/car_detail.html', car=car, visits=visits)



@app.route("/mechanic_dashboard", methods=['GET', 'POST'])
@login_required
def mechanic_dashboard():
    search_query = request.args.get('search', '').strip()
    mechanic_id = current_user.id

    if search_query:
        cars = Car.query.filter(
            (Car.mechanic_id == mechanic_id) &
            (Car.visibility == True) &
            ((Car.registration_number.contains(search_query)) |
             (Car.owner.has(CarOwner.phone_number.contains(search_query))))
        ).all()
    else:
        cars = Car.query.filter_by(mechanic_id=mechanic_id, visibility=True).all()

    for car in cars:
        car.visits.sort(key=lambda visit: visit.date, reverse=True)
    
    return render_template('mechanic/mechanic_dashboard.html', cars=cars)

@app.route("/delete_car/<int:car_id>", methods=["POST"])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.mechanic_id != current_user.id:
        flash('You do not have permission to delete this car.', 'danger')
        return redirect(url_for('mechanic_dashboard'))

    car.visibility = False
    db.session.commit()
    app.logger.info(f'{current_user.username} deleted car {car.registration_number}')
    flash('Car deleted successfully!', 'success')
    return redirect(url_for('mechanic_dashboard'))


@app.route("/update_car/<int:car_id>", methods=['GET', 'POST'])
@login_required
def update_car(car_id):
    car = Car.query.get_or_404(car_id)
    form = UpdateCarForm()
    
    if form.validate_on_submit():
        car.additional_info = form.additional_info.data
        db.session.commit()
        flash('Car details updated successfully!', 'success')
        app.logger.info(f'{current_user.username} updated car {car.registration_number}')

        return redirect(url_for('mechanic_dashboard'))
    
    elif request.method == 'GET':
        form.additional_info.data = car.additional_info
    
    return render_template('mechanic/update_car.html', form=form, car=car)


##########################
#########################
# Speech to text
#######################
#######################
#client = speech.SpeechClient.from_service_account_file(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
#client = speech.SpeechClient.from_service_account_file("/home/yne/flask/instance/google-speech-to-text-key.json")

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

@app.route('/speech_to_text', methods=['POST'])
@login_required
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    audio_content = audio_file.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        enable_automatic_punctuation=True,
        language_code="bg-BG",
        audio_channel_count=1,
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "

    return jsonify({"transcript": transcript.strip()}), 200