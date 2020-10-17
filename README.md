```
1.python -m venv  blog_env
2.blog_env\Scripts\activate
3.pip3 install flask
4.mkdir blog_app
5.blog_app/__init__.py
  from flask import Flask
  app=Flask(__name__)
  from app import routes
6.blog_app/routes.py
  from blog_app import app
  @app.route(‘/’)
  @app.route(‘index’)
  def index():
    return 'hello world' 
7.micro_blog.py
  from blog_app import app
8.cmd:set FLAK_APP=micro_blog.py --告诉flask引入这个，但是每次终端都要设置，引入下面的包来管理
9.pip3 install python-dotenv
10.flask-wtf：集成了表单验证等等
11.安装flask-sqlalchemy是一个orm框架；flask-migrate数据库迁移框架
    flask db init 创建迁移仓库
    flask db migrate -m "create user table" 生成迁移脚本
    flask db upgrade 就把修改的信息在数据库中进行改变
12.pybabel操作
    pybabel extract -F babel.cfg -k _l -o messages.pot .

    pybabel init -i messages.pot -d blog_app/translations -l zh
    pybabel compile -d blog_app/translations
    更新
    (venv) $ pybabel extract -F babel.cfg -k _l -o messages.pot .
    (venv) $ pybabel update -i messages.pot -d app/translations

    flask translate init language
    flask translate update
    flask translate compile
13.blueprint大概是一个子系统，封装了该系统相关的路由、表单、视图函数等等
    开始处于休眠状态，蓝图在注册到app中时，就会把自己的内容传递到app里，相当于临时管理
14.生成requirements.txt
    pip3 freeze > requirements.txt
    pip3 install -r requirements.txt
I:\elasticsearch-7.9.2>.\bin\elasticsearch-service.bat install|start|stop|remove 注册|移除|开启|关闭服务
   
ps -ef | grep elastic
./bin/elasticsearch


yum repolist
yum install 软件名称                  yum -q install /usr/bin/iostat
yum update
yum remove 软件名称
yum list
yum search 关键词
yum info package
yum localinstall *.rpm
yum install oracle-validated

15.更新microblog
(venv) $ git pull                              # download the new version
(venv) $ sudo supervisorctl stop microblog     # stop the current server
(venv) $ flask db upgrade                      # upgrade the database
(venv) $ flask translate compile               # upgrade the translations
(venv) $ sudo supervisorctl start microblog    # start a new server

RQ实现了任务队列

```