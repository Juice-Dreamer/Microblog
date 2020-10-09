from flask import Blueprint

bp = Blueprint(name='auth', import_name=__name__)  # url_for('auth.xxx')

from blog_app.auth import routes
