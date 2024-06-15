# from auction import db,login_manager

# from auction import bcrypt
from flask_login import UserMixin
from datetime import datetime
from auction.connection import db,login_manager,bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model,UserMixin):
    id = db.Column(db.Integer(),primary_key=True)
    username = db.Column(db.String(length=50),unique=True,nullable=False)
    email_address = db.Column(db.String(length=255),nullable=False,unique=True)
    password_hash = db.Column(db.String(length=60),nullable=False)
    budget = db.Column(db.Integer(),nullable=False,default=1000)
    phone_number = db.Column(db.String(length=255),nullable=False)
    items = db.relationship('Item',backref='owned_user',lazy=True)
    sent_mails = db.relationship('Mail',foreign_keys="Mail.sender_id",backref='sender',lazy=True)
    received_mails = db.relationship('Mail', foreign_keys="Mail.receiver_id", backref='receiver', lazy=True)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self,plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password(self,password_for_checking):
        return bcrypt.check_password_hash(self.password_hash,password_for_checking)

    def show_budget(self):
        return round(self.budget,2)

    def can_bid(self,item_obj):
        return self.budget >= item_obj.minimum_next_bid()

    def can_custom_bid(self,item_obj,custom_bid):
        return self.budget >= custom_bid and custom_bid >= item_obj.minimum_next_bid()

    def __repr__(self):
        return f'{self.username}'


class Item(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(length=30),nullable=False,unique=True)
    description = db.Column(db.String(length=1024),nullable=False)
    start = db.Column(db.String(length=30),nullable=False)
    end = db.Column(db.String(length=30), nullable=False)
    current_bid = db.Column(db.Float,nullable=False)
    category = db.Column(db.String(),nullable=False)
    step = db.Column(db.Float,nullable=False)
    seller_id = db.Column(db.Integer())
    bidder_id = db.Column(db.Integer())
    owner = db.Column(db.Integer(),db.ForeignKey('user.id'))
    image = db.Column(db.String(length=255))
    sold = db.Column(db.String(length=10))

    def minimum_next_bid(self):
        return round(self.current_bid * self.step,2)

    def assign_owner(self):
        future_owner = User.query.filter_by(username=self.bidder_id).first()
        self.owner = future_owner

    def __repr__(self):
        return f'{self.name}'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start': self.start,
            'end': self.end,
            'category': self.category,
            'current_bid': self.current_bid,
            'step': self.step,
            'seller_id' : self.seller_id,
            'bidder_id': self.bidder_id,
            'owner': self.owner,
            'image': self.image
        }

class Mail(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    subject = db.Column(db.String(length=30), nullable=False)
    message = db.Column(db.String(length=1024), nullable=False)
    sender_id = db.Column(db.Integer(), db.ForeignKey('user.id'),nullable=False)
    sender_username = db.Column(db.String(length=50), nullable=False)
    receiver_id = db.Column(db.Integer(),db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(length=30), nullable=False)


