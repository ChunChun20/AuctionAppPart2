import base64
import time

from flask_socketio import emit
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
from PIL import Image
import qrcode
from math import ceil
import io
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
            if bid_item_object.owner == None:
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
            else:
                flash(f"Bidding period on {bid_item_object.name[:-6]} is over!", 'fail')

        custom_bid_item = request.form.get('custom_bid_item')
        custom_bid_item_object = Item.query.filter_by(name=custom_bid_item).first()
        if custom_bid_item_object:
            if custom_bid_item_object.owner == None:
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
            else:
                flash(f"Bidding period on {custom_bid_item_object.name[:-6]} is over!", 'fail')

        return redirect(url_for('auction_page'))

    if request.method == 'GET':
        items = Item.query.filter_by(owner=None)
        return render_template('auctions.html',items=items,bid_form=bid_form,custom_bid_form=custom_bid_form)


@app.route('/auctions_bid_mobile',methods=['POST'])
def auctions_bid_mobile():
    data = request.json
    bid_item = data.get('itemName')
    currentUser = data.get('currentUser')



    bid_item_object = Item.query.filter_by(name=bid_item).first()
    user = User.query.filter_by(username=currentUser).first()
    if bid_item_object:
        if user.can_bid(bid_item_object):
            if bid_item_object.bidder_id != None:
                    #refund money if outbid
                old_bidder = User.query.filter_by(username=bid_item_object.bidder_id).first()
                old_bidder.budget += bid_item_object.current_bid
            if bid_item_object.owner:
                return jsonify({'success': False, 'message': f'Bidding period has ended.'}), 200

                #assign highest bidder
            bid_item_object.bidder_id = user.username
            bid_item_object.current_bid = round(bid_item_object.current_bid * bid_item_object.step,2)
            user.budget -= round(bid_item_object.current_bid,2)
            db.session.commit()
            time.sleep(0.5)
            items = Item.query.filter_by(owner=None).all()
            items_dict = [item.to_dict() for item in items]
            print(items_dict)
            socketio.emit('updated_items', items_dict)
            print("Items updated")


            return jsonify({'success': True, 'message': f'Successfully placed bid on {bid_item[:-6]}'}), 200

        else:

            return jsonify({'success': False, 'message': f'Failed to place bid on {bid_item[:-6]}'}), 200


@app.route('/auctions_custom_bid_mobile',methods=['POST'])
def auctions_custom_bid_mobile():
    data = request.json
    custom_bid_item = data.get('itemName')
    currentUser = data.get('currentUser')
    customBid = data.get('customBid')
    print(f"is it empty {custom_bid_item},{currentUser},{customBid}")




    user = User.query.filter_by(username=currentUser).first()
    custom_bid_item_object = Item.query.filter_by(name=custom_bid_item).first()
    if custom_bid_item_object:
        if user.can_custom_bid(custom_bid_item_object, float(customBid)):
            # refund money if outbid
            if custom_bid_item_object.bidder_id != None:
                old_bidder = User.query.filter_by(username=custom_bid_item_object.bidder_id).first()
                old_bidder.budget += custom_bid_item_object.current_bid
            if custom_bid_item_object.owner:
                return jsonify({'success': False, 'message': f'Bidding period has ended.'}), 200

            # assign highest bidder
            custom_bid_item_object.bidder_id = user.username
            custom_bid_item_object.current_bid = float(customBid)
            user.budget -= round(custom_bid_item_object.current_bid, 2)
            db.session.commit()
            time.sleep(0.5)
            items = Item.query.filter_by(owner=None).all()
            items_dict = [item.to_dict() for item in items]
            print(items_dict)
            socketio.emit('updated_items', items_dict)
            print("Items updated")
            return jsonify({'success': True, 'message': f'Successfully placed custom bid on {custom_bid_item[:-6]}'}), 200
        else:

            return jsonify({'success': False, 'message': f'Failed to place custom bid on {custom_bid_item[:-6]}'}), 200


@app.route('/get_next_bid/<string:item_id>', methods=['GET'])
def get_next_bid(item_id):

    item = Item.query.filter_by(id=int(item_id)).first()
    minimum_next_bid = item.minimum_next_bid()

    return jsonify({'success': True, "minimum_next_bid": minimum_next_bid}), 200




@app.route('/auctions_mobile', methods=['GET'])
def auctions_mobile():
    auctions = Item.query.filter_by(owner=None)
    auctions_json = []
    for item in auctions:
        image_path = os.path.join(app.root_path, 'static', 'images', item.image)
        img_data = get_image_data(image_path)
        auction_data = {
            'id': item.id,
            'description': item.description,
            'start': item.start,
            'category': item.category,
            'name': item.name,
            'seller_id': item.seller_id,
            'bid': item.current_bid,
            'end': item.end,
            'highest_bidder': item.bidder_id,
            'image': img_data  # Include image data in the response
        }
        auctions_json.append(auction_data)
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


@app.route('/register_mobile',methods=['POST'])
def register_page_mobile():
    data = request.json
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')
    email = data.get('email_address')
    phone = data.get('phone_number')

    email_address = User.query.filter_by(email_address=email).first()
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'success': False, 'message': 'user already exist'}), 401
    if email_address:
        return jsonify({'success': False, 'message': 'user already exist'}), 401

    if username == "" or len(username) < 6:
        return jsonify({'success': False, 'message': 'invalid username'}), 401

    if email == "" or "@" not in email:
        return jsonify({'success': False, 'message': 'invalid email'}), 401

    if password1 == "" or len(password1) < 7:
        return jsonify({'success': False, 'message': 'invalid password'}), 401

    if password2 == "" or len(password2) < 7:
        return jsonify({'success': False, 'message': 'invalid password'}), 401

    if phone == "" or len(phone) < 10:
        return jsonify({'success': False, 'message': 'invalid phone number'}), 401



    if password1 == password2:
        create_user = User(username=username,
                           email_address=email,
                           password=password1,
                           phone_number=f"+359" + phone[1:])
        db.session.add(create_user)
        db.session.commit()


        return jsonify({'success': True, 'message': 'successfully created user'}), 200
    else:
        # Authentication failed
        return jsonify({'success': False, 'message': 'failed to create user'}), 401


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


url = "https://drive.usercontent.google.com/download?id=1BI7_6wGB0K5ktZ_5B5uIhGanEbuzle5i&export=download&authuser=0"
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
    )
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill='black',back_color='white')

static_folder = os.path.join(app.root_path, 'static')
img_path = os.path.join(static_folder, 'qr_code.png')

    # Save the image
img.save(img_path)

@app.route('/download_mobile_app')
def download_mobile_app():


    return render_template('downloadApp.html')

@app.route('/login_mobile',methods=['POST'])
def login_page_mobile():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user_trying_to_login = User.query.filter_by(username=username).first()
    if user_trying_to_login and user_trying_to_login.check_password(
            password_for_checking=password):
        user_info = {
            'username': user_trying_to_login.username,
            'budget': str(round(user_trying_to_login.budget,2)),
            'id': user_trying_to_login.id
        }


        return jsonify({'success': True, 'user': user_info}), 200
    else:
        # Authentication failed
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401


@app.route('/get_user_data',methods=['POST'])
def get_user_data():
    data = request.json
    user_id = data.get('id')

    user = User.query.filter_by(id=int(user_id)).first()


    user_info = {
        'username': user.username,
        'budget': user.budget,
        'id': user.id,
    }

    return jsonify({'success': True, 'user': user_info}), 200



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

def get_image_data(image_path):
    with Image.open(image_path) as img:
        # Convert the image to RGB mode (remove alpha channel)
        img = img.convert('RGB')
        # Resize and compress the image
        img.thumbnail((600, 600))  # Resize image to fit within 300x300 pixels
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=80)  # Compress the image with JPEG format and 70% quality
        img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return img_data

@app.route('/create_item_mobile',methods=['POST'])
def create_item_mobile_page():
    name = request.form['name']
    category = request.form['category']
    description = request.form['description']
    bid = request.form['bid']
    duration = request.form['duration']
    user_id = request.form['id']

    # Save the image
    image = request.files['image']

    current_time = datetime.now()

    if name == "":
        return jsonify({'success': False, 'message': 'Username too short'}), 401

    if description == "" or len(description) > 1024:
        return jsonify({'success': False, 'message': 'invalid description'}), 401

    if int(bid) <= 0:
        return jsonify({'success': False, 'message': 'invalid starting price'}), 401

    if int(duration) <= 0:
        return jsonify({'success': False, 'message': 'invalid duration'}), 401

    if image == "":
        return jsonify({'success': False, 'message': 'invalid image'}), 401

    image_file = save_image(image)
    random_number = random.randint(100000, 999999)
    create_item = Item(name=name+str(random_number),
                        description=description,
                        start=current_time.strftime("%m/%d/%Y, %H:%M:%S"),
                        end=(current_time + timedelta(minutes=int(duration))).strftime("%m/%d/%Y, %H:%M:%S"),
                        current_bid=float(bid),
                        step=1.10,
                        image=image_file,
                        seller_id = int(user_id),
                        category = category,
                        sold = "False"
                               )



    db.session.add(create_item)
    db.session.commit()


        # flash(f"Successfully created {create_item.name[:-6]}",'success')

    return jsonify({'success': True}), 200



@app.route('/owned_items')
def owned_items_page():
    owned_items = Item.query.filter_by(owner=current_user.id).order_by(desc(Item.end)).all()


    return render_template('owned_items.html',owned_items=owned_items)


@app.route('/owned_items_mobile/<string:user_id>', methods=['GET'])
def owned_items_mobile(user_id):
    page = request.args.get('page', default=1, type=int)
    per_page = 5
    owned_items = Item.query.filter_by(owner=int(user_id)).order_by(desc(Item.end)).paginate(page=page,per_page=per_page)

    owned_items_json = []
    for item in owned_items:
        image_path = os.path.join(app.root_path, 'static', 'images', item.image)
        img_data = get_image_data(image_path)
        owned_items_data = {
            'end': item.end,
            'name': item.name,
            'bid': item.current_bid,
            'category': item.category,
            'description': item.description,
            'id': item.id,
            'image': img_data  # Include image data in the response
        }
        owned_items_json.append(owned_items_data)

    total_pages = ceil(owned_items.total / per_page)

    return jsonify(owned_items=owned_items_json,
                   page=owned_items.page,
                    pages=owned_items.pages,
                    total_pages=total_pages,
                    total_items=owned_items.total)


@app.route('/recently_sold', methods=['GET'])
def recently_sold_items():
    recently_sold = Item.query.filter_by(sold="True").order_by(desc(Item.end)).all()

    return render_template('recently_sold.html', recently_sold=recently_sold)


@app.route('/recently_sold_mobile', methods=['GET'])
def recently_sold_items_mobile():
    page = request.args.get('page', default=1, type=int)
    per_page = 5

    recently_sold = Item.query.filter_by(sold="True").order_by(desc(Item.end)).paginate(page=page,per_page=per_page)

    recently_sold_json = []

    for item in recently_sold.items:  # Iterate over .items, not the paginator object itself
        image_path = os.path.join(app.root_path, 'static', 'images', item.image)
        img_data = get_image_data(image_path)
        recently_sold_data = {
            'category': item.category,
            'name': item.name,
            'bid': item.current_bid,
            'description': item.description,
            'end': item.end,
            'id': item.id,
            'image': img_data  # Include image data in the response
        }
        recently_sold_json.append(recently_sold_data)

    total_pages = ceil(recently_sold.total / per_page)

    return jsonify(
        recently_sold=recently_sold_json,
        page=recently_sold.page,
        pages=recently_sold.pages,
        total_pages=total_pages,
        total_items=recently_sold.total
    )

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

    if form.errors != {}:
        for error in form.errors.values():
            flash(error, 'fail')

    return render_template('resell_page.html', item=item,form=form)



@app.route('/delete_item/<int:item_id>', methods=['POST', 'DELETE'])
def delete_item(item_id):
    if request.method in ['POST', 'DELETE']:

        item = Item.query.filter_by(id=item_id).first()


        db.session.delete(item)
        db.session.commit()

        flash(f"Successfully deleted item '{item.name[:-6]}' ", 'success')

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


    return redirect(url_for('mail_box'))


@app.route('/send_mail_to_seller_mobile', methods=['POST'])
def send_mail_to_seller_mobile():
    data = request.json
    receiver = data.get('sender_id')
    subject = data.get('subject')
    message = data.get('message')
    sender = data.get('receiver_id')
    sender_username = data.get('username')
    current_time = datetime.now()


    timeOfSending = current_time.strftime("%m/%d/%Y, %H:%M:%S")


    create_mail = Mail(
        subject=subject,
        message=message,
        sender_id=sender,
        receiver_id=receiver,
        date=timeOfSending,
        sender_username=sender_username

    )

    db.session.add(create_mail)
    db.session.commit()

    return jsonify({'success': True}), 200



@app.route('/mail_box')
def mail_box():
    mails = Mail.query.filter_by(receiver_id=current_user.id).order_by(desc(Mail.date)).all()

    return render_template('mailbox.html', mails=mails)
@app.route('/mail_box_mobile', methods=['POST'])
def get_user_mail_box():
    data = request.json
    user_id = data.get('id')

    mails = Mail.query.filter_by(receiver_id=int(user_id)).order_by(desc(Mail.date)).all()

    mail_info_list = []
    for mail in mails:
        mail_info = {
            'id': mail.id,
            'subject': mail.subject,
            'message': mail.message,
            'sender': mail.sender_id,
            'sender_username': mail.sender_username,
            'receiver': mail.receiver_id,
            'date': mail.date
        }
        mail_info_list.append(mail_info)


    print(mail_info_list)
    return jsonify({'success': True, 'mails':  mail_info_list}), 200




@app.route('/delete_mail/<int:mail_id>', methods=['POST', 'DELETE'])
def delete_mail(mail_id):
    if request.method in ['POST', 'DELETE']:

        mail = Mail.query.filter_by(id=mail_id).first()


        db.session.delete(mail)
        db.session.commit()

        flash(f"Successfully deleted mail from user {mail.sender_username}", 'success')

        return redirect(url_for('mail_box'))


@app.route('/delete_mail_mobile/<string:mail_id>', methods=['DELETE'])
def delete_mail_mobile(mail_id):

    mail_to_be_deleted = Mail.query.filter_by(id=int(mail_id)).first()
    db.session.delete(mail_to_be_deleted)
    db.session.commit()

    return jsonify({'success': True}), 200

@app.route('/delete_item_mobile/<string:item_id>', methods=['DELETE'])
def delete_item_mobile(item_id):
        item = Item.query.filter_by(id=int(item_id)).first()


        db.session.delete(item)
        db.session.commit()


        return jsonify({'success': True}), 200





thread = threading.Thread(target=check_auctions)
thread.start()
