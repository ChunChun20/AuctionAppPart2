#to make changes in the db type this in terminal
#from auction import app,db
#app.app_context().push()
#db.drop_all()
import time

from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_bcrypt import Bcrypt
# from flask_login import LoginManager
from flask_socketio import SocketIO
from auction.models import Item
from auction.connection import db,login_manager,bcrypt




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction.db'
app.config['SECRET_KEY'] = 'ea3dfe510eafebf0ae34717a'
# db = SQLAlchemy(app)
db.init_app(app)
# bcrypt = Bcrypt(app)
bcrypt.init_app(app)
login_manager.init_app(app)
socketio = SocketIO(app)




@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on("update_items")
def update_items():
    time.sleep(0.5)
    items = Item.query.filter_by(owner=None).all()
    items_dict = [item.to_dict() for item in items]
    print(items_dict)
    socketio.emit('updated_items',items_dict)
    print("Items updated")



from auction import routes


