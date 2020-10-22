from flask import render_template, request
from blog_app.errors import bp
from blog_app import db
from blog_app.api.errors import error_response as api_error_response


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)  # 装饰器变成蓝图的
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template("errors/500.html"), 500  # 默认返回200状态码，可以不用写
