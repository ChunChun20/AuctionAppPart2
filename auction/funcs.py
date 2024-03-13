import time
from datetime import datetime
import random
from flask import redirect, url_for

from auction.models import Item,User
# from auction import db,app
from auction import app
from auction.connection import db
from twilio.rest import Client
import auction.keys

# def check_auction(item_obj):
#     today = date.today()
#     now = today.strftime("%m/%d/%Y, %H:%M:%S")
#     if now >= item_obj.end:
#         new_owner = User.query.filter_by(username=item_obj.bidder_id).first()
#         item_obj.owner = new_owner.id
#         db.session.commit()
#
# schedule.every(1).seconds.do(check_auction)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)

# def check_auction(item_obj):
#     current_date = datetime.now()
#     current_date1 = datetime.strftime(current_date, "%m/%d/%Y, %H:%M:%S")
#     if current_date1 > item_obj.end:
#         new_owner = User.query.filter_by(username=item_obj.bidder_id).first()
#         item_obj.owner = new_owner.id
#         db.session.commit()

client = Client(auction.keys.account_sid,auction.keys.auth_token)

def check_auctions():
    while True:
        with app.app_context():
            items = Item.query.filter_by(owner=None)

            for item in items:
                current_date = datetime.now()
                current_date1 = datetime.strftime(current_date, "%m/%d/%Y, %H:%M:%S")
                if current_date1 > item.end and item.bidder_id == None:
                    db.session.delete(item)
                    db.session.commit()

                elif current_date1 > item.end and item.bidder_id != None:
                    # random_number = random.randint(100000, 999999)
                    prev_owner = User.query.filter_by(id=item.seller_id).first()
                    new_owner = User.query.filter_by(username=item.bidder_id).first()
                    item.owner = new_owner.id
                    prev_owner.budget += item.current_bid
                    item.sold = "True"
                    # item.name = item.name + str(random_number)
                    db.session.commit()
                    try:
                        message = client.messages.create(
                            to=new_owner.phone_number,
                            from_=auction.keys.twilion_number,
                            body=f"Congratulations {new_owner}! You successfully won {item.name[:-6]} for {item.current_bid}$"
                        )
                        print(message.body)
                    except:
                        print("No more money to send SMS")


        time.sleep(2)

