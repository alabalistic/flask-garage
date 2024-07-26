# public.py

from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import current_user, login_required
from app import app, db
from app.forms import PostForm, CommentForm
from app.models import Post, Comment, Car, User, Role, RepairShopImage


@app.context_processor
def inject_mechanics():
    mechanics = User.query.filter(User.roles.any(Role.name == 'mechanic')).all()
    return dict(mechanics=mechanics)

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    form = PostForm()
    return render_template('home.html', posts=posts, form=form)

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/garage")
def garage():
    return render_template('garage.html', title='Garage', cars=Car.query.all())

@app.route("/posts")
def posts():
    all_posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('posts.html', posts=all_posts)

@app.route("/post/new", methods=['POST'])
#@login_required
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
            flash('Само механици могат да отговарят на запитвания.', 'danger')
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

@app.route("/edit_comment/<int:comment_id>", methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash('You do not have permission to edit this comment.', 'danger')
        return redirect(url_for('home'))

    form = CommentForm()
    if form.validate_on_submit():
        comment.content = form.content.data
        db.session.commit()
        flash('Your comment has been updated!', 'success')
        return redirect(url_for('post', post_id=comment.post_id))
    elif request.method == 'GET':
        form.content.data = comment.content

    return render_template('edit_comment.html', form=form, comment=comment)

@app.route("/delete_comment/<int:comment_id>", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash('You do not have permission to delete this comment.', 'danger')
        return redirect(url_for('home'))

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('post', post_id=post_id))

# public.py

@app.route("/edit_post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('home'))

    form = PostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.content.data = post.content

    return render_template('edit_post.html', form=form, post=post)

@app.route("/delete_post/<int:post_id>", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('home'))

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/privacy")
def privacy():
    return render_template('privacy.html', title='Политика за поверителност')

@app.route("/terms")
def terms():
    return render_template('terms.html', title='Условия за ползване')
