from blog_app import mail, current_app
from flask_mail import Message
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():  # 创建application.context
        mail.send(msg)  # mail.send()需要一些app.config的值，就需要application context


def send_mail(subject, sender, recipients, text_body, html_body):
    msg = Message(subject=subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body # current_app是context-aware variable, 无法使用此对象，需要访问代理对象中的真正app
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()  # 异步调用发送邮件

