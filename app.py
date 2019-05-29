#! /usr/bin/env python
import os
import urllib
import requests
import base64
import datetime
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
# import grovepi
# from picamera import PiCamera
import time
import json

threshold_light = 20
threshold_ranger = 20
global_rate = 1
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


class Account(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    deposit = db.Column(db.REAL)

    def __str__(self):
        return self.name


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    spot = db.Column(db.Integer)
    plate = db.Column(db.TEXT)
    start = db.Column(db.TEXT)
    end = db.Column(db.TEXT)
    rate = db.Column(db.REAL)

    def __str__(self):
        return self.name


class Spot(db.Model):
    spot_id = db.Column(db.INTEGER, primary_key=True, unique=True)
    status = db.Column(db.INTEGER)
    start_time = db.Column(db.TEXT)
    rate = db.Column(db.REAL)

    def __str__(self):
        return self.name


class Vehicle(db.Model):
    plate = db.Column(db.TEXT, primary_key=True, unique=True)
    user_id = db.Column(db.INTEGER, unique=True)
    status = db.Column(db.INTEGER)
    spot = db.Column(db.INTEGER)
    category = db.Column(db.TEXT)
    color = db.Column(db.TEXT)
    brand = db.Column(db.TEXT)

    def __str__(self):
        return self.plate


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
        response = urllib.urlopen(url)
        contents = response.read()
        return app.response_class(contents, content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)

# Get Temperature Information
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
        response = urllib.urlopen(url)
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
    led_spot1 = 2
    led_spot2 = 3
    led_spot3 = 4
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
        for i in range(len(status)):
            Spot.query.filter_by(spot_id=i+1).update({'status': status[i]})
        db.session.commit()
        contents = {'status': status}
        return app.response_class(json.dumps(contents), content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)


# Get Car Status
@app.route("/carStatus")
def check_car_status():
    #try:
    user_email = str(current_user)
    user = User.query.filter_by(email=user_email).first()
    vehicle_information = Vehicle.query.filter_by(user_id=user.id).first()
    if vehicle_information.status == 1:
        spot_status = Spot.query.filter_by(spot_id=vehicle_information.spot).first()
        contents = {'status': vehicle_information.status, 'spot': vehicle_information.spot,
                    'start_time': spot_status.start_time,
                    'rate': spot_status.rate, 'spot_status': spot_status.status}
        return app.response_class(json.dumps(contents), content_type='application/json')
    else:
        contents = {'status': vehicle_information.status}
        return app.response_class(json.dumps(contents), content_type='application/json')
    # except Exception as e:
    #     contents = {'error': str(e)}
    #     return app.response_class(contents, content_type='application/json', status=404)


# Get Parking History
@app.route("/history")
def get_spot_history():
    try:
        user_email = str(current_user)
        user_info = db.session.query(User).filter_by(email=user_email).first()
        user_role = db.session.query(roles_users).filter_by(user_id=user_info.id).first()
        if user_role.role_id == 2:
            history_record = db.session.query(Record).all()
        else:
            history_record = db.session.query(Record).filter_by(user_id=user_info.id).all()
        contents = {}
        for i in range(len(history_record)):
            column = {'id': history_record[i][0], 'user_id': history_record[i][1],
                      'spot': history_record[i][2], 'plate': history_record[i][3],
                      'start_time': history_record[i][4],
                      'end_time': history_record[i][5], 'rate': history_record[i][6]}
            contents[str(i)] = column
        return app.response_class(json.dumps(contents), content_type='application/json')
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
    return 0


def check_entrance_status():
    # Connect the Grove Light Sensor to analog port
    # SIG,NC,VCC,GND
    light_sensor_in = 1
    light_sensor_out = 2
    grovepi.pinMode(light_sensor_in, "INPUT")
    grovepi.pinMode(light_sensor_out, "INPUT")
    camera = PiCamera()
    camera.resolution = (1024, 768)
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
                in_vehicle = Vehicle.query.filter_by(plate=in_plate).first()
                if in_vehicle is None:
                    display("No permit in!")
                else:
                    spot = search_spot()
                    if spot != -1:
                        in_spot = Spot.query.filter_by(spot_id=spot).first()
                        display("Welcome in!\n" + "Spot:" + in_spot.spot_id)
                        # tai gan
                        in_vehicle.status = 1
                        in_vehicle.spot = spot
                        in_spot.status = 1
                        in_spot.start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        in_spot.rate = global_rate
                        db.session.commit()
                        while grovepi.analogRead(light_sensor_in) > threshold_light:
                            time.sleep(2)
                        # fang gan
                    else:
                        display("No vacant spot!")
            if exit_value < threshold_light:
                time.sleep(2)
                while True:
                    if len(plate_recognize()) < 10:
                        out_plate = plate_recognize()
                        break
                    time.sleep(2)
                out_vehicle = Vehicle.query.filter_by(plate=out_plate).first()
                out_spot = Spot.query.filter_by(spot_id=out_vehicle).first()
                out_account = Account.query.filter_by(user_id=out_vehicle.user_id).first()
                end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                start_time = datetime.datetime.strptime(out_spot.start_time, '%Y-%m-%d %H:%M:%S')
                fee = (end_time - start_time).total_seconds() * out_spot.rate
                if out_account.deposit < fee:
                    display("No sufficient fund!")
                else:
                    display("See you next time!\n" + "Plate:" + out_vehicle.plate)
                    # tai gan
                    out_account.deposit -= fee
                    new_record = Record(user_id=out_vehicle.user_id, spot=out_vehicle.spot, plate=out_vehicle.plate,
                                        start=out_spot.start_time, end=str(datetime.datetime.now()), rate=out_spot.rate)
                    Record.add(new_record)
                    out_vehicle.status = 0
                    out_vehicle.spot = 0
                    out_spot.status = 1
                    out_spot.start_time = None
                    out_spot.rate = global_rate
                    db.session.commit()
                    while grovepi.analogRead(light_sensor_out) > threshold_light:
                        time.sleep(2)
                    # fang gan
            return
        except Exception as e:
            return e


def camera_capture():
    camera = PiCamera()
    camera.resolution = (1024, 768)
    camera.start_preview()
    file_name = time.asctime(time.localtime(time.time()))
    camera.capture('images/' + file_name + '.jpg')
    return file_name


def plate_recognize():
    try:
        # Sample image file is available at http://plates.openalpr.com/ea7the.jpg
        file_name = camera_capture()
        image_path = os.path.abspath(os.path.dirname(__file__)) + '/image/' + file_name + 'jpg'
        secret_key = 'sk_24c51607925c2471ba30d290'
        with open(image_path, 'rb') as image_file:
            img_base64 = base64.b64encode(image_file.read())
        url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s' % secret_key
        r = requests.post(url, data=img_base64)
        r = r.json()
        plate_result = r["results"][0]["plate"]
        return plate_result
    except Exception as e:
        return e


# send command to display (no need for external use)
def text_command(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)


def display(word):
    import time, sys
    if sys.platform == 'uwp':
        import winrt_smbus as smbus
        bus = smbus.SMBus(1)
    else:
        import smbus
        import RPi.GPIO as GPIO
        rev = GPIO.RPI_REVISION
        if rev == 2 or rev == 3:
            bus = smbus.SMBus(1)
        else:
            bus = smbus.SMBus(0)

    # this device has two I2C addresses
    DISPLAY_RGB_ADDR = 0x62
    DISPLAY_TEXT_ADDR = 0x3e
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 1, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0x08, 0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 4, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 3, 128)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 2, 64)
    text_command(0x01)  # clear display
    time.sleep(.05)
    text_command(0x08 | 0x04)  # display on, no cursor
    text_command(0x28)  # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in word:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            text_command(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR, 0x40, ord(c))


def search_spot():
    if Spot.query.filter_by(spot_id=1).first().status == 0:
        return 1
    if Spot.query.filter_by(spot_id=2).first().status == 0:
        return 2
    if Spot.query.filter_by(spot_id=3).first().status == 0:
        return 3
    return -1


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

