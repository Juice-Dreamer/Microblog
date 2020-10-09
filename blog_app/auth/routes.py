from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _, lazy_gettext as _l
from blog_app import db
from blog_app.auth import bp
from blog_app.auth.forms import LoginForm, RegisterForm, ResetPasswordForm, ResetPasswordRequestForm
from blog_app.models import User
from blog_app.auth.email import send_password_reset_email


@bp.route('/login', methods=['POST', 'GET'])  # 接受get post请求
def login():
    if current_user.is_authenticated:  # current_user是从session里取出来的【可能是数据库，也可能是匿名用户】 is_authenticated就是检测是否登录
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():  # get时返回false，就执行render_template
        user = User.query.filter_by(username=form.username.data).first()  # User继承了db.Models类 就可以访问query等属性
        if user is None or not user.check_password(form.password.data):
            flash(_l('Invalid username or password!'))  # 向用户返回提交信息
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)  # 把当前用户登录情况存入session
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':  # netloc检测是否相对或者绝对路径，免得重定向到恶意地址
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template("auth/login.html", title='Sign in', form=form)  # post就返回这个


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_l('Congratulations! you can log with it now!'))
        return redirect(url_for('auth.login'))
    return render_template("auth/register.html", title='Sign up', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:  # 用户已登录，重定向到index
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(_l('Check your email to reset your password.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_l('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
