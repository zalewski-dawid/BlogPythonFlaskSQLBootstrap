from functools import wraps
from flask_ckeditor.utils import cleanify
from urllib import request
from datetime import date,datetime
from flask import Flask,render_template,url_for,flash,redirect,session,abort,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_mail import Mail,Message
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey,Boolean,Date
from werkzeug.security import generate_password_hash, check_password_hash
from forms import NewPostForm, RegisterForm, LoginForm, CommentForm, EditInfoForm, ContactForm,EditCommentForm
from dotenv import load_dotenv
import os


load_dotenv()

secret_key = os.environ.get('SECRET_KEY')
email=os.environ.get('EMAIL')
email_password=os.environ.get('EMAIL_PASSWORD')


#CONFIGURING ENV
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
ckeditor = CKEditor(app)
Bootstrap5(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail=Mail(app)

#CONFIGURING LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id==int(user_id))).scalar()


#Decorator created for not allowing users accessibility to some routes e.g creating new post, only admin has so many privileges
def admin_only(func):
    @wraps(func)
    def decorated_function(*args,**kwargs):
        #IF ID is not equal to 1 then return abort with 403 error
        if not current_user.is_authenticated or current_user.id!=1:
            return abort(403)

        return func(*args,**kwargs)
    return decorated_function



#CREATING DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
db=SQLAlchemy(app)


#CONFIGURING TABLES

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    title:Mapped[str]=mapped_column(String(250),unique=True,nullable=False)
    subtitle:Mapped[str]=mapped_column(String(250),nullable=False)
    date:Mapped[str]=mapped_column(String(250),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    author:Mapped[str]=relationship('User',back_populates='posts')
    img_url:Mapped[str]=mapped_column(String(250),nullable=False)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(50),nullable=False,unique=True)
    password:Mapped[str]=mapped_column(String(250),nullable=False)
    username:Mapped[str]=mapped_column(String(50),nullable=False,unique=True)
    avatar=mapped_column(String(250),nullable=False)
    created_at: Mapped[date] = mapped_column(Date, default=date.today)
    bio:Mapped[str]=mapped_column(String(50),nullable=True,default="Tech enjoyer")
    posts=relationship("BlogPost",back_populates="author")



class Comment(db.Model):
    __tablename__ = 'comments'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    username:Mapped[str]=mapped_column(String(50),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    author_avatar:Mapped[str]=mapped_column(String(250),nullable=False)
    post_id:Mapped[int]=mapped_column(Integer, db.ForeignKey('blog_posts.id'))
    likes:Mapped[int]=mapped_column(Integer,nullable=True,default=0)
    dislikes:Mapped[int]=mapped_column(Integer,nullable=True,default=0)



class LikesDislikes(db.Model):
    __tablename__ = 'likes_dislikes'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    commenter_id:Mapped[int]=mapped_column(Integer,unique=False)
    comment_id:Mapped[int]=mapped_column(Integer,unique=False)
    liked:Mapped[bool]=mapped_column(Boolean,unique=False,default=False)
    disliked:Mapped[bool]=mapped_column(Boolean,unique=False,default=False)


#CREATING ALL TABLES
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    result=db.session.query(BlogPost).all()

    return render_template("index.html",all_posts=result)



@app.route('/about')
def about():
    return render_template("about.html")




@app.route('/contact',methods=["GET","POST"])
def contact():
    form = ContactForm()
    if request.method == "POST":
        #sending email message
        email_to_send=os.getenv('MAIL_USERNAME')
        email_sender=form.email.data
        name_to_send=form.name.data
        message_to_send=form.message.data
        msg=Message(
            subject=f"Contact Form from {name_to_send} {email_sender}",
            body=message_to_send,
            recipients=[email_to_send]
        )

        try:
            mail.send(msg)
            flash('Your message has been sent successfully!.','success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'An error occured: {str(e)}','error')


    return render_template("contact.html",form=form)




@app.route('/new-post',methods=["GET","POST"])
@admin_only
def new_post():
    form = NewPostForm()
    if form.validate_on_submit():

        New_Post=BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id
        )
        db.session.add(New_Post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template("new-post.html",form=form,span_content="New Post")




@app.route('/register',methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        hash_and_salted_password=generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        new_user=User(
            email=form.email.data,
            password=hash_and_salted_password,
            username=form.username.data,
            avatar=form.avatar.data
        )
        if not db.session.query(User).filter_by(email=form.email.data).first():
            if not db.session.query(User).filter_by(username=form.username.data).first():
                if len(form.username.data)<=50:
                    if len(form.email.data)<=50:
                        if len(form.password.data)<=250:
                            db.session.add(new_user)
                            db.session.commit()
                            login_user(new_user)
                            return redirect(url_for('index'))
                        else:
                            flash("Too long password, max 250 char", "ERROR")
                            return redirect(url_for('register'))
                    else:
                        flash("Too long email, max 50 char", "ERROR")
                        return redirect(url_for('register'))
                else:
                    flash("Too long username, max 50 char", "ERROR")
                    return redirect(url_for('register'))


            else:
                flash("Username already registered","ERROR")
                return redirect(url_for('register'))

        else:
            flash("Email already registered","ERROR")
            return redirect(url_for('login'))





    return render_template("register.html",form=form)




@app.route('/login',methods=["GET","POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=form.email.data).first():
            result=db.session.query(User).filter_by(email=form.email.data).first()
            if check_password_hash(result.password,form.password.data):
                user=db.session.query(User).filter_by(email=form.email.data).first()
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("WRONG PASSWORD","ERROR")
                return redirect(url_for('login'))

        else:
            flash("WRONG EMAIL","ERROR")
            return redirect(url_for('login'))



    return render_template("login.html",form=form)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))




@app.route('/post/<int:post_id>',methods=["GET","POST"])
@login_required
def show_post(post_id):
    post=db.session.query(BlogPost).filter_by(id=post_id).first()
    form=CommentForm()
    all_comments=db.session.query(Comment).filter_by(post_id=post_id).all()
    if form.validate_on_submit():
        new_comment=Comment(
            username=current_user.username,
            body=form.comment.data,
            author_avatar=current_user.avatar,
            user_id=current_user.id,
            post_id=post_id,
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post.id))
    return render_template("post.html",post=post,form=form,all_comments=all_comments)



@app.route('/edit-post/<int:post_id>',methods=["GET","POST"])
@admin_only
def edit_post(post_id):
    form=NewPostForm()
    post = db.session.query(BlogPost).filter_by(id=post_id).first()
    if form.validate_on_submit():
        #UPDATING DATA
        post.title=form.title.data
        post.subtitle=form.subtitle.data
        post.date=date.today().strftime("%B %d, %Y")
        post.body=form.body.data
        post.img_url=form.img_url.data
        db.session.commit()
        return redirect(url_for('show_post',post_id=post.id))

    #Filling already existing data into form

    form.title.data=post.title
    form.subtitle.data=post.subtitle
    form.body.data=post.body
    form.img_url.data=post.img_url
    return render_template("new-post.html",span_content="Edit post",form=form)




@app.route('/handling-reactions/<int:comment_id>/<string:reaction>/<int:commenter_id>/<int:post_id>',methods=["GET","POST"])
@login_required
def handling_reactions(comment_id,reaction,commenter_id,post_id):
    comment = db.session.query(Comment).filter_by(id=comment_id).first()

    #if particular commenter haven't had already commented
    if not db.session.query(LikesDislikes).filter_by(commenter_id=commenter_id,comment_id=comment_id).first() :

        if reaction=="like":

            comment.likes+=1
            new_commenter=LikesDislikes(
                commenter_id=commenter_id,
                comment_id=comment_id,
                liked=True,
            )
            db.session.add(new_commenter)
            db.session.commit()




        else:

            comment.dislikes+=1
            new_commenter=LikesDislikes(
                commenter_id=commenter_id,
                comment_id=comment_id,
                disliked=True,
            )
            db.session.add(new_commenter)
            db.session.commit()

    #if particular commenter want to delete like or dislike
    else:
        result=db.session.query(LikesDislikes).filter_by(commenter_id=commenter_id,comment_id=comment_id).first()
        if reaction=="like":
            if result.liked==True and result.disliked==False:
                comment.likes-=1
                db.session.delete(result)
                db.session.commit()

        else:
            if result.liked==False and result.disliked==True:
                comment.dislikes-=1
                db.session.delete(result)
                db.session.commit()


    #return back
    return redirect(url_for('show_post',post_id=post_id)+f'#com{comment_id}')


@app.route("/dashboard/<username>")
@login_required
def profile_dashboard(username):
    result=db.session.query(User).filter_by(username=username).first()
    email=result.email
    username=result.username
    bio=result.bio
    date=result.created_at
    avatar=result.avatar



    return render_template("profile-dashboard.html",email=email,username=username,bio=bio,date=date,avatar=avatar)


@app.route("/edit-user-info/<username>/<int:user_id>",methods=["GET","POST"])
@login_required
def edit_user_info(username,user_id):
    form=EditInfoForm()
    #this condition is for allowing only account owner to manage info about profile
    if current_user.username==username:
        if request.method=="POST":
            user_x_name=form.username.data
            bio=form.bio.data
            avatar_url=form.avatar.data
            if not db.session.query(User).filter_by(username=user_x_name).first():
                if len(user_x_name)<=50 and len(user_x_name)>0:
                    if len(bio)<=50 and len(bio)>0:
                        result=db.session.query(User).filter_by(id=user_id).first()
                        result.username=user_x_name
                        result.bio=bio
                        if avatar_url!="":
                            result.avatar=avatar_url
                        db.session.commit()
                        return redirect(url_for('profile_dashboard',username=user_x_name))
                    else:
                        flash("Too long BIO, max 50 char", "ERROR")
                        return redirect(url_for("edit_user_info", username=username, user_id=user_id))
                else:
                    flash("Too long username, max 50 char", "ERROR")
                    return redirect(url_for("edit_user_info", username=username, user_id=user_id))


            else:
                flash("This username is already taken")
                return redirect(url_for("edit_user_info",username=username,user_id=user_id))


        return render_template("edit-user-info.html",form=form)



@app.route("/edit-comment/<int:comment_id>/<int:post_id>",methods=["GET","POST"])
@login_required
def edit_comment(comment_id,post_id):
    result=db.session.query(Comment).filter_by(id=comment_id).first()

    if current_user.id==result.user_id:
        form=EditCommentForm()
        if request.method=="GET":
            form.comment.data=result.body

        if form.validate_on_submit():
            edited_content=form.comment.data
            print(edited_content)
            comment=db.session.query(Comment).filter_by(id=comment_id).first()
            comment.body=edited_content
            print(comment.body)
            db.session.commit()
            #come back to the previous page
            return redirect(url_for('show_post',post_id=post_id))
    else:
        return redirect(url_for('index'))

    return render_template("edit-comment.html",form=form)








if __name__ == '__main__':
    app.run(debug=True)