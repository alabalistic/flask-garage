# public.py

from app import app, db
from app.forms import PostForm, CommentForm
from app.models import Post, Comment, Car, User  # Import the User model
from flask import render_template, url_for, flash, redirect, request, jsonify  # Add request to the import
from flask_login import current_user, login_required

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    form = PostForm()  # Initialize the form here
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
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        user_id = current_user.id if current_user.is_authenticated else User.query.filter_by(username='Анонимен потребител').first().id
        post = Post(content=form.content.data, user_id=user_id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
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
def get_comments(post_id):
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

