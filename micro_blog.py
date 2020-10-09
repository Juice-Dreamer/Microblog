from blog_app import create_app, db, cli
from blog_app.models import User, Post

app = create_app()  # 创建app
cli.register(app)  # 添加指令


@app.shell_context_processor  # 让下面的函数变成shell context function；flask shell 就会执行这个注册
def make_shell_context():  # 添加数据库实例和model到shell context中
    return {
        'db': db,
        'User': User,
        'Post': Post
    }
