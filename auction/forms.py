from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired,FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField,PasswordField,SubmitField,FloatField,IntegerField,SelectField
from wtforms.validators import Length,EqualTo,Email,DataRequired,ValidationError
from auction.models import User,Item

class UserRegisterForm(FlaskForm):

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists!')

    def validate_email_address(self,email):
        email_address = User.query.filter_by(email_address=email.data).first()
        if email_address:
            raise ValidationError('Email Address already exists!')

    username = StringField(label='Username:',validators=[Length(max=30),DataRequired()])
    email_address = StringField(label='Email Address:',validators=[Email(),DataRequired()])
    password1 = PasswordField(label='Password:',validators=[Length(min=7),DataRequired()])
    password2 = PasswordField(label='Confirm Password: ',validators=[EqualTo('password1'),DataRequired()])
    phone_number = StringField(label="Phone number: ",validators=[Length(min=10),DataRequired()])
    submit = SubmitField(label='Create Account')



class ItemRegisterForm(FlaskForm):

    def validate_name(self,name):
        item_name = Item.query.filter_by(name=name.data).first()
        if item_name:
            raise ValidationError('Item name already exists!')



    name = StringField(label='Item name:',validators=[Length(max=30),DataRequired()])
    description = StringField(label='Description',validators=[Length(max=1250),DataRequired()])
    current_bid = FloatField(label='Starting bid:',validators=[DataRequired()])
    duration = IntegerField(label='Auction duration(days): ',validators=[DataRequired()])
    photo = FileField(label="Upload an image",validators=[DataRequired()])

    category_choices = [("Others", "Others"),("Watches", "Watches"), ("Books", "Books"), ("Accessories", "Accessories"),("Clothes", "Clothes"),("Art", "Art"),("Music", "Music"),("Gifts", "Gifts")]
    category = SelectField(label='Category:', choices=category_choices, validators=[DataRequired()])

    submit = SubmitField(label='Create')

class LoginForm(FlaskForm):
    username = StringField(label='Username: ',validators=[DataRequired()])
    password = PasswordField(label='Password: ', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')

class BidForm(FlaskForm):
    submit = SubmitField(label='Bid now!')

class CustomBidForm(FlaskForm):
    custom_bid = FloatField(label='Enter your bid: ',validators=[DataRequired()])
    submit = SubmitField(label='Place Custom Bid now!')

class ItemResellForm(FlaskForm):

    # def validate_name(self,name):
    #     item_name = Item.query.filter_by(name=name.data).first()
    #     if item_name:
    #         raise ValidationError('Item name already exists!')



    name = StringField(label='Item name:',validators=[Length(max=30),DataRequired()])
    description = StringField(label='Description',validators=[Length(max=1250),DataRequired()])
    current_bid = FloatField(label='Starting bid:',validators=[DataRequired()])
    duration = IntegerField(label='Auction duration(days): ',validators=[DataRequired()])
    photo = FileField(label="Upload an image",validators=[DataRequired()])

    category_choices = [("Others", "Others"),("Watches", "Watches"), ("Books", "Books"), ("Accessories", "Accessories"),("Clothes", "Clothes"),("Art", "Art"),("Music", "Music"),("Gifts", "Gifts")]
    category = SelectField(label='Category:', choices=category_choices, validators=[DataRequired()])

    submit = SubmitField(label='Create')