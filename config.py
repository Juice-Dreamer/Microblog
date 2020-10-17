import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))  # 预先加载环境变量


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or '123456'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 避免每次改变数据库都向app发送报告信息，这是不需要的一些flask-sqlalchemy特性
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIN_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None  # 加密建立连接的bool
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['1606445662@qq.com', '357861080@qq.com']
    POST_PER_PAGE = 3
    LANGUAGES = ['en', 'zh']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'
    REDIS_URL=os.environ. get('REDIS_URL') or 'redis://'
