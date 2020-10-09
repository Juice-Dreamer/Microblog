from flask import render_template
from blog_app.errors import bp
from blog_app import db


@bp.errorhandler(404)  # 装饰器变成蓝图的
def not_found_error(error):
    return render_template("errors/404.html"), 404


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500  # 默认返回200状态码，可以不用写
