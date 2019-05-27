#!venv/bin/python
import os
import urllib.request
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, current_user
from flask_security.utils import hash_password
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from flask_admin import BaseView, expose
from multiprocessing import Process
import time
import json
<<<<<<< HEAD
=======


>>>>>>> 912543700d571ae89d4103329e8b6420dfa6b666

threshold_light = 20
threshold_ranger = 20
# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

account = db.Table(
    'account',
    db.Column('userid', db.Integer, primary_key=True),
    db.Column('deposit', db.Column(db.REAL))
)

record = db.Table(
    'record',
    db.Column('id', db.Integer, primary_key=True, unique=True, autoincrement=True),
    db.Column('spot', db.Integer),
    db.Column('plate', db.TEXT, unique=True),
    db.Column('start', db.TEXT),
    db.Column('end', db.TEXT),
    db.Column('rate', db.REAL),
)

vehicle = db.Table(
    'vehicle',
    db.Column('plate', db.TEXT, primary_key=True, unique=True),
    db.Column('userid', db.INTEGER, unique=True),
    db.Column('status', db.INTEGER),
    db.Column('spot', db.INTEGER),
    db.Column('category', db.TEXT),
    db.Column('color', db.TEXT),
    db.Column('brand', db.TEXT),
)

spot = db.Table(
    'spot',
    db.Column('spot_id', db.INTEGER, primary_key=True, unique=True),
    db.Column('status', db.INTEGER),
    db.Column('start_time', db.TEXT),
    db.Column('end_time', db.TEXT),
    db.Column('fee', db.REAL),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)











# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))
    # can edit = True
    edit_modal = True
    create_modal = True    
    can_export = True
    can_view_details = True
    details_modal = True


class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    # form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list


class CustomView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/custom_index.html')

# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Get Weather Information
@app.route('/weather')
def get_weather_api():
    url = "http://api.openweathermap.org/data/2.5/weather" \
          "?zip=98467,us&appid=18673bd31365411ca390843bed5b6cba&units=Imperial"
    try:
        response = urllib.request.urlopen(url)
        contents = response.read()
        return app.response_class(contents, content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)

# # Get Temperature Information
@app.route('/temperature')
def get_temperature():
    sensor = 7
    try:
        [temp, hum] = grovepi.dht(sensor, 0)
        if ((math.isnan(temp) == False) and (math.isnan(hum) == False) and (hum >= 0)):
            add_readings(temp, hum)
    except IOError:
        print("An error has occured.")

    except Exception as e:
        print(e)
    return 0

# Get Gas Price
@app.route("/gas")
def get_gas_price():
    url = "http://devapi.mygasfeed.com/stations/details/103920/rfej9napna.json"
    try:
        response = urllib.request.urlopen(url)
        contents = response.read()
        return app.response_class(contents, content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)

# Get Parking Spot Status
@app.route("/spotStatus")
def check_spot_status():
<<<<<<< HEAD
    # Connect the Grove Light Sensor to analog port
    # SIG,NC,VCC,GND
    light_sensor_spot1 = 1

    # Connect the motion sensor to digital port
    # SIG,NC,VCC,GND
    ranger_sensor_spot2 = 5
    ranger_sensor_spot3 = 6

    # Connect the LED to digital port
    # SIG,NC,VCC,GND
    led_spot1 = 1
    led_spot2 = 2
    led_spot3 = 3
    # Turn on LED once sensor exceeds threshold resistance
    grovepi.pinMode(light_sensor_spot1, "INPUT")
    grovepi.pinMode(ranger_sensor_spot2, "INPUT")
    grovepi.pinMode(ranger_sensor_spot3, "INPUT")
    grovepi.pinMode(led_spot1, "OUTPUT")
    grovepi.pinMode(led_spot2, "OUTPUT")
    grovepi.pinMode(led_spot3, "OUTPUT")

    try:
        # Get sensor value
        spot1_value_light = grovepi.analogRead(light_sensor_spot1)
        spot2_value_ranger = ultrasonicRead(ranger_sensor_spot2)
        spot3_value_ranger = ultrasonicRead(ranger_sensor_spot2)
        if spot1_value_light < threshold_light:
            digitalWrite(led_spot1, 1)
            spot1_status = 1
        else:
            digitalWrite(led_spot1, 0)
            spot1_status = 0
        if spot2_value_ranger < threshold_ranger:
            digitalWrite(led_spot2, 1)
            spot2_status = 1
        else:
            digitalWrite(led_spot2, 0)
            spot2_status = 0
        if spot3_value_ranger < threshold_ranger:
            digitalWrite(led_spot3, 1)
            spot3_status = 1
        else:
            digitalWrite(led_spot3, 0)
            spot3_status = 0
        status = [spot1_status, spot2_status, spot3_status]
        contents = {'status': status}
        return app.response_class(json.dumps(contents), content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)
=======
    parked={'status':[0,1,1,0,0,1]}


    return app.response_class(json.dumps(parked,), content_type='application/json')
>>>>>>> 912543700d571ae89d4103329e8b6420dfa6b666

# Get Car Status
@app.route("/carStatus")
def check_car_status():
    try:
        user_email = current_user
        user = db.session.query(User).filter_by(email=user_email)
        vehicle_information = db.session.query(vehicle).filter_by(userid=user.id)
        if vehicle_information.status == 1:
            spot_status = db.session.query(spot).filter_by(spot_id=vehicle_information.spot)
            contents = {'status': vehicle_information.status, 'start_time': spot_status.start_time,
                        'fee': spot_status.fee, 'spot_status': spot_status.status}
            return app.response_class(contents, content_type='application/json')
        else:
            contents = {'status': vehicle_information.status}
            return app.response_class(contents, content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)


# Get Parking History
@app.route("/history")
def get_spot_history():
    try:
        user_email = current_user
        user = db.session.query(User).filter_by(email=user_email)
        history_record = db.session.query(record).filter_by(id=user.id).all()
        return 0
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)

# Get Parking Spot Usage
@app.route("/usage")
def get_spot_usage():
    return 0

# Get Daily Revenue
@app.route("/revenue")
def get_daily_revenue():
    return 0


def check_entrance_status():
    # Connect the Grove Light Sensor to analog port
    # SIG,NC,VCC,GND
    lightsensorin = 2
    lightsensorout = 3


    grovepi.pinMode(lightsensorin, "INPUT")
    grovepi.pinMode(lightsensorout, "INPUT")
    while True:
        try:
            # Get sensor value
            entrance_value = grovepi.analogRead(lightsensorin)
            exit_value = grovepi.analogRead(lightsensorout)


        except Exception as e:
            contents = e
            return app.response_class(contents, content_type='application/json', status=404)


# Create admin
admin = flask_admin.Admin(
    app,
    'My Dashboard',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(Role, db.session, menu_icon_type='fa', menu_icon_value='fa-server', name="Roles"))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(CustomView(name="Custom view", endpoint='custom', menu_icon_type='fa',
                          menu_icon_value='fa-connectdevelop',))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


def f():
    while True:
        print('while loop')
        time.sleep(1)


if __name__ == '__main__':
    p = Process(target=f)
    p.start()
    app.run(debug=True)
    # Build a sample db on the fly, if one does not exist yet.

