from blog_app import db
from flask import current_app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from blog_app import login
from hashlib import md5
import jwt
from time import time
import json
import rq
import redis
from blog_app.search import query_index, add_to_index, remove_from_index

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


# userMixIn实现了基本的验证方法，如是否授权、是否已登录等等
class User(UserMixin, db.Model):  # 数据库表命是snake case 如user，GoodList-->good_list
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), index=True, unique=True)
    about_me = db.Column(db.String(100))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author',
                            lazy='dynamic')  # 声明一对多的关系 arg1代表many方，backref p.author=the user
    # 声明多对多的关系，followed并不是user实例的属性，是sqlAlchemy对象
    # A---followed---followers---follower--->B(暂定)
    # arg1=B,class User=A
    # secondary:the relationship
    # backref定义了如何从右侧实体来访问relationship
    # lazy就是右侧对象sql查询模式，直到具体请求才查询
    # 最后一个参数是左侧的查询模式
    # user1.followed.append(user2) 1关注了2
    followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    message_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='author', lazy='dynamic')
    message_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='recipient',
                                       lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):  # 利用这个网址生成头像,默认是identicon
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        """
        查询关注的所有人的博客以及自己的博客
        """
        followed_posts = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id
        )
        own_posts = Post.query.filter_by(user_id=self.id)
        return followed_posts.union(own_posts).order_by(
            Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        """
        生成token，有效期10分钟
        """
        return jwt.encode({
            'reset_password': self.id, 'exp': expires_in + time()
        }, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        """
        添加一个任务到队列中
        :param name: 任务函数名，如blog_app.tasks.example
        :param description: 呈现给用户的简要描述
        :param args: 任务函数需要的参数
        :param kwargs:
        :return:
        """
        rq_job = current_app.task_queue.enqueue('blog_app.tasks' + name, self.id, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_ion_progress(self,name):
        return Task.query.filter_by(name=name,user=self,complete=False).first()

    @staticmethod
    def verify_reset_password_token(token):
        """
        验证token是否有效
        """
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, page_size):  # 类方法，使用SearchableMixin.search()调用
        """
        根据ids查询出所有的post、总数，并按照id排序
        """
        ids, total = query_index(cls.__tablename__, expression, page, page_size)  # 一般都会把表名作为index name
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total  # db.case(when, value=cls.id)让查询出来的Post按照id顺序

    @classmethod
    def before_commit(cls, session):
        """
        在sqlalchemy commit之前执行，查看是进行了何种操作
        """
        session._changes = {
            'add': list(session.new),  # 添加对象
            'update': list(session.dirty),  # 修改对象
            'delete': list(session.deleted)  # 删除对象
        }

    @classmethod
    def after_commit(cls, session):
        """
        在sqlalchemy commit之后执行，修改elasticsearch中的index
        """
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        """
        刷新所有post的index
        """
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)  # commit之前执行
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)  # commit之后执行


class Post(SearchableMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # sqlalchemy自己调用方法
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))
    __searchable__ = ['body']

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 最后阅读时间

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(self.payload_json)


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


@login.user_loader
def load_user(id):
    """
    flask-login会跟踪每一个用户情况，每个用户都会分一块内存，每当一个新用户登录并导航到某个页面时，就会根据id加载其对应的信息
    由于flask-login不知道数据库情况，因此需要app来加载一个user
    """
    return User.query.get(int(id))
