from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField

class NewPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    img_url = StringField('Image URL', validators=[DataRequired(),URL()])
    body = CKEditorField('Blog Content', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    avatar= StringField('Avatar URL', validators=[DataRequired(),URL()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CommentForm(FlaskForm):
    comment=CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField('Comment')

class EditInfoForm(FlaskForm):
    username=StringField('Username')
    bio=StringField('Bio')
    avatar=StringField('Avatar URL', validators=[URL()])
    submit = SubmitField('Edit Info')

class ContactForm(FlaskForm):
    name=StringField('Name', validators=[DataRequired()])
    email=StringField('Email', validators=[DataRequired(), Email()])
    message=TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class EditCommentForm(FlaskForm):
    comment=CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField('Edit')
