import time

from sqlalchemy import desc

# from auction import app,db
from auction import app, socketio
from auction.connection import db
from datetime import datetime,timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from auction.models import Item, User, Mail
from auction.forms import UserRegisterForm,ItemRegisterForm,LoginForm,BidForm,CustomBidForm,ItemResellForm
from flask_login import login_user,logout_user,login_required,current_user
from auction.funcs import check_auctions
import threading,random
import os




@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/auctions',methods=['GET','POST'])
@login_required
def auction_page():
    bid_form = BidForm()
    custom_bid_form = CustomBidForm()
    if request.method == 'POST':
        bid_item = request.form.get('bid_item')
        bid_item_object = Item.query.filter_by(name=bid_item).first()
        if bid_item_object:
            if current_user.can_bid(bid_item_object):
                if bid_item_object.bidder_id != None:
                    #refund money if outbid
                    old_bidder = User.query.filter_by(username=bid_item_object.bidder_id).first()
                    old_bidder.budget += bid_item_object.current_bid
                #assign highest bidder
                bid_item_object.bidder_id = current_user.username
                bid_item_object.current_bid = round(bid_item_object.current_bid * bid_item_object.step,2)
                current_user.budget -= round(bid_item_object.current_bid,2)
                db.session.commit()
                flash(f"Successfully placed a bid on {bid_item_object.name[:-6]}!",'success')
            else:
                flash(f"Your bid on: {bid_item_object.name[:-6]} failed!",'fail')

        custom_bid_item = request.form.get('custom_bid_item')
        custom_bid_item_object = Item.query.filter_by(name=custom_bid_item).first()
        if custom_bid_item_object:
            if current_user.can_custom_bid(custom_bid_item_object,custom_bid_form.custom_bid.data):
                # refund money if outbid
                if custom_bid_item_object.bidder_id != None:
                    old_bidder = User.query.filter_by(username=custom_bid_item_object.bidder_id).first()
                    old_bidder.budget += custom_bid_item_object.current_bid
                # assign highest bidder
                custom_bid_item_object.bidder_id = current_user.username
                custom_bid_item_object.current_bid = custom_bid_form.custom_bid.data
                current_user.budget -= round(custom_bid_item_object.current_bid,2)
                db.session.commit()

                flash(f"Successfully placed a bid on {custom_bid_item_object.name[:-6]}!",'success')
            else:
                flash(f"Please place a higher bid!",'fail')

        return redirect(url_for('auction_page'))

    if request.method == 'GET':
        items = Item.query.filter_by(owner=None)
        return render_template('auctions.html',items=items,bid_form=bid_form,custom_bid_form=custom_bid_form)

@app.route('/auctions_mobile', methods=['GET'])
def auctions_mobile():
    auctions = Item.query.filter_by(owner=None)
    auctions_json = [{'category': item.category, 'name': item.name, 'bid': item.current_bid,'end': item.end, 'highest_bidder': item.bidder_id} for item in auctions]
    return jsonify(auctions=auctions_json)






@app.route('/auctions/<string:category>',methods=['GET','POST'])
@login_required
def auction_page_categories(category):
    bid_form = BidForm()
    custom_bid_form = CustomBidForm()
    if request.method == 'POST':
        bid_item = request.form.get('bid_item')
        bid_item_object = Item.query.filter_by(name=bid_item).first()
        if bid_item_object:
            if current_user.can_bid(bid_item_object):
                if bid_item_object.bidder_id != None:
                    #refund money if outbid
                    old_bidder = User.query.filter_by(username=bid_item_object.bidder_id).first()
                    old_bidder.budget += bid_item_object.current_bid
                #assign highest bidder
                bid_item_object.bidder_id = current_user.username
                bid_item_object.current_bid = round(bid_item_object.current_bid * bid_item_object.step,2)
                current_user.budget -= round(bid_item_object.current_bid,2)
                db.session.commit()
                flash(f"Successfully placed a bid on {bid_item_object.name}!",'success')
            else:
                flash(f"Your bid on: {bid_item_object.name[:-6]} failed!",'fail')

        custom_bid_item = request.form.get('custom_bid_item')
        custom_bid_item_object = Item.query.filter_by(name=custom_bid_item).first()
        if custom_bid_item_object:
            if current_user.can_custom_bid(custom_bid_item_object,custom_bid_form.custom_bid.data):
                # refund money if outbid
                if custom_bid_item_object.bidder_id != None:
                    old_bidder = User.query.filter_by(username=custom_bid_item_object.bidder_id).first()
                    old_bidder.budget += custom_bid_item_object.current_bid
                # assign highest bidder
                custom_bid_item_object.bidder_id = current_user.username
                custom_bid_item_object.current_bid = custom_bid_form.custom_bid.data
                current_user.budget -= round(custom_bid_item_object.current_bid,2)
                db.session.commit()

                flash(f"Successfully placed a bid on {custom_bid_item_object.name[:-6]}!",'success')
            else:
                flash(f"Please place a higher bid!",'fail')

        print(category)
        return redirect(url_for('auction_page_categories',category=category))

    if request.method == 'GET':

        items = Item.query.filter_by(owner=None,category=category)
        return render_template('auctions_categories.html',items=items,bid_form=bid_form,custom_bid_form=custom_bid_form,category=category)




@app.route('/register',methods=['GET','POST'])
def register_page():
    form = UserRegisterForm()
    if form.validate_on_submit():
        create_user = User(username=form.username.data,
                           email_address=form.email_address.data,
                           password=form.password1.data,
                           phone_number=f"+359" + form.phone_number.data[1:])
        db.session.add(create_user)
        db.session.commit()
        login_user(create_user)
        flash("Account created successfully!",'success')
        return redirect(url_for('auction_page'))
    if form.errors != {}: #if there are not errors from validations
        for error in form.errors.values():
            flash(error,'fail')
    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user_trying_to_login = User.query.filter_by(username=form.username.data).first()
        if user_trying_to_login and user_trying_to_login.check_password(
                password_for_checking=form.password.data
        ):
            login_user(user_trying_to_login)
            flash(f'Successfully logged as {user_trying_to_login.username}!','success')
            return redirect(url_for('auction_page'))
        else:
            flash("Wrong username or password!",'fail')
    return render_template('login.html',form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("Successfully logged out!",'info')
    return redirect(url_for('login_page'))


@app.route('/create',methods=['GET','POST'])
def create_page():
    current_time = datetime.now()

    form = ItemRegisterForm()
    if form.validate_on_submit():
        image_file = save_image(form.photo.data)
        random_number = random.randint(100000, 999999)
        create_item = Item(name=form.name.data+str(random_number),
                           description=form.description.data,
                           start=current_time.strftime("%m/%d/%Y, %H:%M:%S"),
                           end=(current_time + timedelta(minutes=form.duration.data)).strftime("%m/%d/%Y, %H:%M:%S"),
                           current_bid=form.current_bid.data,
                           step=1.10,
                           image=image_file,
                           seller_id = current_user.id,
                           category = form.category.data,
                            sold = "False"
                           )



        db.session.add(create_item)
        db.session.commit()


        flash(f"Successfully created {create_item.name[:-6]}",'success')

        return redirect(url_for('auction_page'))

    if form.errors != {}: #if there are not errors from validations
        for error in form.errors.values():
            flash(error,'fail')
    return render_template('create.html',form=form)

def save_image(picture_file):
    picture=picture_file.filename
    picture_path = os.path.join(app.root_path,'static/images',picture)
    picture_file.save(picture_path)
    return picture


@app.route('/owned_items')
def owned_items_page():
    owned_items = Item.query.filter_by(owner=current_user.id)

    return render_template('owned_items.html',owned_items=owned_items)


@app.route('/recently_sold', methods=['GET'])
def recently_sold_items():
    recently_sold = Item.query.filter_by(sold="True")
            
    return render_template('recently_sold.html', recently_sold=recently_sold)


@app.route('/recently_sold_mobile', methods=['GET'])
def recently_sold_items_mobile():
    recently_sold = Item.query.filter_by(sold="True")
    recently_sold_json = [{'category': item.category, 'name': item.name, 'bid': item.current_bid} for item in recently_sold]
    return jsonify(recently_sold=recently_sold_json)



@app.route('/resell/<int:item_id>', methods=['GET', 'POST'])
def resell_page(item_id):
    current_time = datetime.now()


    form = ItemResellForm()
    item = Item.query.filter_by(id=item_id).first()
    # default_image_url = url_for('static', filename='images/' + item.image)

    # print(default_image_url)
    form.name.default = item.name[:-6]
    form.description.default = item.description
    form.current_bid.default = item.current_bid
    # form.photo.default = default_image_url

    form.data['name'] = item.name[:-6]
    form.data['description'] = item.description
    form.data['current_bid'] = item.current_bid

    if request.method == 'GET':
        form.process()


    if form.validate_on_submit():
        image_file = save_image(form.photo.data)
        random_number = random.randint(100000, 999999)
        create_item = Item(name=form.name.data+str(random_number),
                           description=form.description.data,
                           start=current_time.strftime("%m/%d/%Y, %H:%M:%S"),
                           end=(current_time + timedelta(minutes=form.duration.data)).strftime("%m/%d/%Y, %H:%M:%S"),
                           current_bid=form.current_bid.data,
                           step=1.10,
                           image=image_file,
                           seller_id=current_user.id,
                           category=form.category.data,
                           sold="False"
                           )
        # item.owner = None
        # db.session.add(item)
        db.session.add(create_item)
        db.session.commit()

        flash(f"Successfully added {create_item.name[:-6]} back to the market", 'success')

        return redirect(url_for('auction_page'))

    if form.errors != {}:  # if there are not errors from validations
        for error in form.errors.values():
            flash(error, 'fail')

    return render_template('resell_page.html', item=item,form=form)



@app.route('/delete_item/<int:item_id>', methods=['POST', 'DELETE'])
def delete_item(item_id):
    if request.method in ['POST', 'DELETE']:

        item = Item.query.filter_by(id=item_id).first()


        db.session.delete(item)
        db.session.commit()


        return redirect(url_for('owned_items_page'))



@app.route('/send_mail_to_seller', methods=['POST'])
def send_mail_to_seller():
    current_time = datetime.now()


    seller_id = request.form.get('seller_id')  # Assuming you have a user ID in your form
    subject = request.form.get('subject')
    message = request.form.get('message')
    timeOfSending = current_time.strftime("%m/%d/%Y, %H:%M:%S")

    # Broadcasting the message to a specific room (user)

    create_mail = Mail(
        subject=subject,
        message=message,
        sender_id=current_user.id,
        receiver_id=seller_id,
        date=timeOfSending,
        sender_username=current_user.username

    )

    db.session.add(create_mail)
    db.session.commit()

    seller = User.query.filter_by(id=seller_id).first()

    flash(f"Successfully sent mail to user {seller.username} ", 'success')

    print(f"{seller_id},{subject},{message}")


    return redirect(url_for('auction_page'))



@app.route('/mail_box')
def mail_box():
    mails = Mail.query.filter_by(receiver_id=current_user.id).order_by(desc(Mail.date)).all()

    return render_template('mailbox.html', mails=mails)


@app.route('/delete_mail/<int:mail_id>', methods=['POST', 'DELETE'])
def delete_mail(mail_id):
    if request.method in ['POST', 'DELETE']:

        mail = Mail.query.filter_by(id=mail_id).first()


        db.session.delete(mail)
        db.session.commit()


        return redirect(url_for('mail_box'))





thread = threading.Thread(target=check_auctions)
thread.start()
