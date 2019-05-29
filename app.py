#!venv/bin/python
import os
import urllib.request
import requests
import base64
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
    db.Column('deposit', db.REAL)
)

record = db.Table(
    'record',
    db.Column('id', db.Integer, primary_key=True, unique=True, autoincrement=True),
    db.Column('user_id', db.Integer),
    db.Column('spot', db.Integer),
    db.Column('plate', db.TEXT),
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


# Get Car Status
@app.route("/carStatus")
def check_car_status():
    try:
        user_email = str(current_user)
        user = User.query.filter_by(email=user_email).first()
        vehicle_information = db.session.query(vehicle).filter_by(userid=user.id).first()
        if vehicle_information.status == 1:
            spot_status = db.session.query(spot).filter_by(spot_id=vehicle_information.spot).first()
            contents = {'status': vehicle_information.status, 'spot': vehicle_information.spot,
                        'start_time': spot_status.start_time,
                        'fee': spot_status.fee, 'spot_status': spot_status.status}
            return app.response_class(json.dumps(contents), content_type='application/json')
        else:
            contents = {'status': vehicle_information.status}
            return app.response_class(json.dumps(contents), content_type='application/json')
    except Exception as e:
        contents = {'error': str(e)}
        return app.response_class(contents, content_type='application/json', status=404)
# tess = db.session.query(vehicle).filter_by(userid=1).first()
# tess.status = 0
# db.session.commit()
# Get Parking History
@app.route("/history")
def get_spot_history():
    try:
        user_email = str(current_user)
        user_info = db.session.query(User).filter_by(email=user_email).first()
        user_role = db.session.query(roles_users).filter_by(user_id=user_info.id).first()
        if user_role.role_id == 2:
            history_record = db.session.query(record).all()
        else:
            history_record = db.session.query(record).filter_by(user_id=user_info.id).all()
        contents = json.dumps({})

        for i in range(len(history_record)):
            column = {'id': history_record[i][0], 'user_id': history_record[i][1],
                      'spot': history_record[i][2], 'plate': history_record[i][3],
                      'start_time': history_record[i][4],
                      'end_time': history_record[i][5], 'rate': history_record[i][6]}
            contents = json.dumps({**json.loads(contents), **{str(i): column}})
        return app.response_class(contents, content_type='application/json')
    except Exception as e:
        contents = {"Error": str(e)}
        return app.response_class(json.dumps(contents), content_type='application/json', status=404)

# Get Parking Spot Usage
@app.route("/usage")
def get_spot_usage():
    return 0

# Get Daily Revenue
@app.route("/revenue")
def get_daily_revenue():
    return app.response_class(str(current_user))


def check_entrance_status():
    # Connect the Grove Light Sensor to analog port
    # SIG,NC,VCC,GND
    light_sensor_in = 2
    light_sensor_out = 3

    grovepi.pinMode(light_sensor_in, "INPUT")
    grovepi.pinMode(light_sensor_out, "INPUT")
    while True:
        try:
            # Get sensor value
            entrance_value = grovepi.analogRead(light_sensor_in)
            exit_value = grovepi.analogRead(light_sensor_out)
            if entrance_value < threshold_light:
                time.sleep(2)
                while True:
                    if len(plate_recognize()) < 10:
                        in_plate = plate_recognize()
                        break
                    time.sleep(2)
                return
            if exit_value < threshold_light:
                time.sleep(2)
                while True:
                    if len(plate_recognize()) < 10:
                        out_plate = plate_recognize()
                        break
                    time.sleep(2)
                return
        except Exception as e:
            contents = {'error': e}
            return app.response_class(contents, content_type='application/json', status=404)


def plate_recognize():
    try:
        # Sample image file is available at http://plates.openalpr.com/ea7the.jpg
        image_path = os.path.abspath(os.path.dirname(__file__)) + '\image\car2.jpeg'
        # pi use image_path = '../image/car2.jpeg'
        secret_key = 'sk_24c51607925c2471ba30d290'
        with open(image_path, 'rb') as image_file:
            img_base64 = base64.b64encode(image_file.read())
        url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s' % (secret_key)
        r = requests.post(url, data=img_base64)
        r = r.json()
        plate_result = r["results"][0]["plate"]
        return plate_result
    except Exception as e:
        return e


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

