from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, g, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import get_locale, lazy_gettext as _l
from guess_language import guess_language
from blog_app import db
from blog_app.main.forms import EditProfileForm, PostForm, EmptyForm, MessageForm
from blog_app.models import User, Post, Message, Notification
from blog_app.main import bp
from blog_app.translate import translate
from blog_app.main.forms import SearchForm


@bp.before_request
def before_request():
    """
    在请求前做一些通用处理，在执行view function之前执行：用户刚好要登录时记录当前时间
    """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()  # 把修改写入数据库，这里不需要session.add()，再执行一次也得到是current_user对象
        g.locale = str(get_locale())  # 为了翻译datetime
        g.search_form = SearchForm()  # g可以存储一些需要保存到请求结束的数据，每个请求和客户端的g是不一样的，因此可以保存每个请求的私有数据


@bp.route('/', methods=['POST', 'GET'])
@bp.route('/index', methods=['POST', 'GET'])
@login_required  # 必须强制登录才可访问
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_l('Successfully write a post!'))
        return redirect(url_for('main.index'))  # 标准写法，需要重定向，而不是通过render_template返回index页面，可以减少浏览器刷新，否则刷新浏览器就会提示重新提交表单
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POST_PER_PAGE'],
                                                   False)  # 查询当前用户关注的人以及自己的post .paginate(1,20,False)分页查询
    # 超过页码返回empty-False 否则返回404-True
    next_url = url_for('main.index',
                       page=posts.next_num) if posts.has_next else None  # Pagination对象其他有用方法：has_next、has_prev、next_num、prev_num
    prev_url = url_for('main.index',
                       page=posts.prev_num) if posts.has_prev else None  # url_for可以任意添加关键字参数，不在路径中Flask会自动变成query参数
    return render_template('index.html', title='Home', form=form, posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')  # 动态URL
@login_required
def user(username):
    print('重定向到此处')
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POST_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_l('Your changes have been saved!'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title='edit profile', form=form)


@bp.route('/follow/<username>', methods=['GET', 'POST'])
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_l('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_l('You cannot follow yourself.'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)  # 关注该用户
        db.session.commit()
        flash(_l('Successfully followed %(username)s.', username=user.username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['GET', 'POST'])
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():  # 只能验证submit提交的post请求
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_l('User %(username)s not found.', username=username))
            return redirect(url_for('main.user', username=username))
        if user == current_user:
            flash(_l('You cannot unfollow yourself.'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_l('Successfully unfollowed %(username)s.', username=user.username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))  # CSRF token is missing or invalid


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POST_PER_PAGE'],
                                                                False)  # 查询当前用户关注的人以及自己的post .paginate(1,20,False)分页查询
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template("index.html", title="Explore", posts=posts.items, next_url=next_url,
                           prev_url=prev_url)  # posts.items才能拿到分页数据 Pagination对象


@bp.route('/search')  # 默认get请求
@login_required
def search():
    if not g.search_form.validate():  # 不会检测数据怎么提交，为空则不通过
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POST_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) if total > page * current_app.config[
        'POST_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) if page > 1 else None
    return render_template('search.html', title=_l('Search'), posts=posts, next_url=next_url, prev_url=prev_url)


@bp.route('/translate', methods=['POST'])
def translate_post():
    return jsonify(
        {'text': translate(request.form['text'], request.form['source_language'], request.form['dest_language'])})


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    """
    hover username and show the detail information.
    :param username:
    :return:
    """
    user = User.query.filter_by(username=username).first()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_l('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_l('Send Message'), form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.message_received.order_by(Message.timestamp.desc()).paginate(page, current_app.config[
        'POST_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(
        Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
