# public.py

from app import app, db
from app.forms import PostForm, CommentForm
from app.models import Post, Comment, Car, User, Role
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import current_user, login_required
from google.cloud import speech
import os

@app.context_processor
def inject_mechanics():
    mechanics = User.query.filter(User.roles.any(Role.name == 'mechanic')).all()
    return dict(mechanics=mechanics)

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    form = PostForm()
    return render_template('public/home.html', posts=posts, form=form)

@app.route("/about")
def about():
    return render_template('public/about.html', title='About')

@app.route("/garage")
def garage():
    return render_template('mechanic/garage.html', title='Garage', cars=Car.query.all())

@app.route("/posts")
def posts():
    all_posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('posts.html', posts=all_posts)

@app.route("/post/new", methods=['POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        user_id = current_user.id if current_user.is_authenticated else User.query.filter_by(username='Анонимен').first().id
        post = Post(content=form.content.data, user_id=user_id)
        db.session.add(post)
        db.session.commit()
        flash('Поста е създаден успешно', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated and (current_user.id == post.user_id or current_user.is_mechanic()):
            comment = Comment(content=form.content.data, user_id=current_user.id, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been added!', 'success')
            return redirect(url_for('post', post_id=post.id))
        else:
            flash('You do not have permission to comment on this post.', 'danger')
    comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template('post.html', post=post, form=form, comments=comments)

@app.route("/post/<int:post_id>/comments", methods=['GET'])
def get_post_comments(post_id):
    post = Post.query.get_or_404(post_id)
    limit = request.args.get('limit', type=int)
    if limit:
        comments = Comment.query.filter_by(post_id=post.id).limit(limit).all()
    else:
        comments = Comment.query.filter_by(post_id=post.id).all()
    comments_data = [{
        'author': {
            'username': comment.author.username,
            'image_file': comment.author.image_file
        },
        'content': comment.content,
        'date_posted': comment.date_posted.strftime('%Y-%m-%d %H:%M')
    } for comment in comments]
    return jsonify({'comments': comments_data})

@app.route("/mechanic/<int:mechanic_id>")
def mechanic_profile(mechanic_id):
    mechanic = User.query.get_or_404(mechanic_id)
    if not mechanic.is_mechanic():
        flash('This user is not a mechanic.', 'danger')
        return redirect(url_for('home'))
    return render_template('public/mechanic_profile.html', mechanic=mechanic)

@app.route("/search", methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    
    if query:
        posts = Post.query.filter(Post.content.ilike(f'%{query}%')).order_by(Post.date_posted.desc()).all()
        mechanics = User.query.filter(User.roles.any(Role.name == 'mechanic'), User.username.ilike(f'%{query}%')).all()
        comments = Comment.query.filter(Comment.content.ilike(f'%{query}%')).order_by(Comment.date_posted.desc()).all()
    else:
        posts = []
        mechanics = []
        comments = []
    
    return render_template('search_results.html', posts=posts, mechanics=mechanics, comments=comments, query=query)

@app.route('/speech_to_text', methods=['POST'])
@login_required
def speech_to_text():
    if not current_user.is_mechanic():
        return jsonify({"error": "Access denied"}), 403

    if 'audio' not in request.files or 'channels' not in request.form:
        return jsonify({"error": "No audio file or channel count provided"}), 400

    audio_file = request.files['audio']
    audio_content = audio_file.read()
    channels = int(request.form['channels'])

    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        return jsonify({"error": "Google application credentials not set"}), 500

    client = speech.SpeechClient.from_service_account_file(credentials_path)

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="bg-BG",
        audio_channel_count=channels,
        sample_rate_hertz=48000,
    )

    try:
        response = client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        return jsonify({"transcript": transcript.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500