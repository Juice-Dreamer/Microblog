from flask import Blueprint

bp = Blueprint(name="errors", import_name=__name__)

from blog_app.errors import handlers  # 避免循环依赖
