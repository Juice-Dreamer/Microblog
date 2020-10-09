from flask import Blueprint

bp = Blueprint(name='main', import_name=__name__)

from blog_app.main import routes
