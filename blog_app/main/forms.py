from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_babel import _, lazy_gettext as _l
from blog_app.models import User
from flask import request


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[DataRequired(), Length(min=0, max=100)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, origin_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.origin_username = origin_username

    def validate_username(self, username):
        if username.data != self.origin_username:
            user = User.query.filter_by(username=self.username.data).first()  # 根据表单输入的名字判断是否重名
            if user is not None:
                raise ValidationError(_l('Please use a different username.'))


class EmptyForm(FlaskForm):
    """
    要在不提交任何数据的情况下 点击 follow or unfollow实现功能
    """
    submit = SubmitField(_l('Follow'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something...'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class SearchForm(FlaskForm):
    """
    搜索框只需要一个文本域，在url中拼接成q=xxx
    """
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:  # form.hidden_tag()会增加这个字段，设置为false，才可点击搜索
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message', validators=[DataRequired(), Length(min=0, max=140)]))
    submit = SubmitField(_l('Submit'))
