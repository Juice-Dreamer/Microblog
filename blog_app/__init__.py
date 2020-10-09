from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from elasticsearch import Elasticsearch

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'  # 非法访问网页要强制登录，flask-login就需要知道哪个是login函数，以此来实现逻辑
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    from blog_app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)  # 注册错误处理蓝图
    from blog_app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')  # 注册授权处理蓝图，login的路径就是 localhost:5000/auth/login
    from blog_app.main import bp as main_bp
    app.register_blueprint(main_bp, template_folder='templates')  # 注册main蓝图

    app.elasticsearch=Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None
    print('是否配置elasticsearch？',app.elasticsearch)
    if not app.debug and not app.testing:  # 调试模式和测试模式都不打印日志
        # 把错误信息发送至邮箱
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                                       fromaddr=app.config['ADMINS'][0], toaddrs=app.config['ADMINS'][1],
                                       subject='MicroBlog Failure', credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        # 处理日志文件
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(filename='logs/microblog.log', maxBytes=10240, backupCount=5)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('MicroBlog startup')

        return app


@babel.localeselector
def get_locale():
    """
    每个请求都会调用这个函数，来设置语言
    """
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from blog_app import models
