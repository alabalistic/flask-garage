# public.py

from app import app, db
from app.forms import PostForm, CommentForm
from app.models import Post, Comment, Car
from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('public/home.html', posts=posts)


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

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated and (current_user.id == post.user_id or current_user.is_mechanic()):
        comment = Comment(content=form.content.data, user_id=current_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
        return redirect(url_for('post', post_id=post.id))
    comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template('post.html', title=post.title, post=post, form=form, comments=comments)
