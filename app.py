#! /usr/bin/env python
import os
import urllib
import requests
import base64
from picamera import PiCamera
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
import grove_rgb_lcd
import grovepi
import datetime
import time
import json
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import logging
import nexmo
import glob
import urllib3


threshold_light = 100
threshold_ranger = 10
global_rate = 0.1
file_name = ""

# Connect the Grove Light Sensor to analog port
# SIG,NC,VCC,GND
light_sensor_spot1 = 0
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

host = 'hc8t32.messaging.internetofthings.ibmcloud.com'
username = 'use-token-auth'
#occupancy
clientid_occ = 'd:hc8t32:Sensors:Occupancy'
password_occ = 'XdA@g*6NkKsR4_cZ*J'
topic_occ = 'iot-2/evt/occupancy/fmt/json'
client_occ = mqtt.Client(clientid_occ)
client_occ.username_pw_set(username, password_occ)
client_occ.connect(host, 1883, 60)
#temperature_humidity
clientid_temp = 'd:hc8t32:Sensors:temp_hum'
password_temp = 'u_LdYE6)@hhtCl7C5E'
topic_temp = 'iot-2/evt/temp/fmt/json'
client_temp = mqtt.Client(clientid_temp)
client_temp.username_pw_set(username, password_temp)
client_temp.connect(host, 1883, 60)
#fee
clientid_fee = 'd:hc8t32:Sensors:fee'
password_fee = ')*pyj@G!RS2oSerFNd'
topic_fee = 'iot-2/evt/fee/fmt/json'
client_fee = mqtt.Client(clientid_fee)
client_fee.username_pw_set(username, password_fee)

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
        return self.user_id


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    spot = db.Column(db.Integer)
    plate = db.Column(db.TEXT)
    start = db.Column(db.TEXT)
    end = db.Column(db.TEXT)
    rate = db.Column(db.REAL)

    def __str__(self):
        return self.id


class Spot(db.Model):
    spot_id = db.Column(db.INTEGER, primary_key=True, unique=True)
    status = db.Column(db.INTEGER)
    start_time = db.Column(db.TEXT)
    rate = db.Column(db.REAL)

    def __str__(self):
        return self.spot_id


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
    

@app.route('/monitor')
def monitor():
    return render_template('admin/monitor.html')


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
        client_fee.publish(topic_temp, json.dumps({'Temperature':temp,'Humidity':hum}))
        contents = {'temperature': temp, 'humidity': hum}
        return app.response_class(json.dumps(contents), content_type='application/json')
    except Exception as e:
        contents = e
        return app.response_class(contents, content_type='application/json', status=404)

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
    

    #try:
    # Get sensor value
    spot1_value_light = grovepi.analogRead(light_sensor_spot1)
    spot2_value_ranger = grovepi.ultrasonicRead(ranger_sensor_spot2)
    spot3_value_ranger = grovepi.ultrasonicRead(ranger_sensor_spot3)
    if spot1_value_light < threshold_light:
        grovepi.digitalWrite(led_spot1, 1)
        spot1_status = 1
    else:
        grovepi.digitalWrite(led_spot1, 0)
        spot1_status = 0
    if spot2_value_ranger < threshold_ranger:
        grovepi.digitalWrite(led_spot2, 1)
        spot2_status = 1
    else:
        grovepi.digitalWrite(led_spot2, 0)
        spot2_status = 0
    if spot3_value_ranger < threshold_ranger:
        grovepi.digitalWrite(led_spot3, 1)
        spot3_status = 1
    else:
        grovepi.digitalWrite(led_spot3, 0)
        spot3_status = 0
    status = [spot1_status, spot2_status, spot3_status]
    occupancy = (spot1_status + spot2_status + spot3_status)/6.0 *100.0
    client_occ.publish(topic_occ, json.dumps({'occupancy':str(occupancy)}))
    for i in range(len(status)):
        Spot.query.filter_by(spot_id=i+1).update({'status': status[i]})
    db.session.commit()
    
    contents = {'status': status}
    return app.response_class(json.dumps(contents), content_type='application/json')
    #except Exception as e:
     #   contents = e
     #   return app.response_class(contents, content_type='application/json', status=404)

@app.route("/picture")
def picture_preview():
    picture_path = os.path.abspath(os.path.dirname(__file__)) + '/image/'
    files = os.listdir(picture_path)
    path_for_picture = [os.path.join(picture_path, basename) for basename in files]
    picture = max(path_for_picture, key=os.path.getctime)
    p = open(picture, 'r')
    f=p.read()
    p.close()
    return app.response_class(f,content_type='image/jpeg')



# Get Car Status
@app.route("/carStatus")
def check_car_status():
    #try:
    user_email = str(current_user)
    user = User.query.filter_by(email=user_email).first()
    vehicle_information = Vehicle.query.filter_by(user_id=user.id).first()
    account=Account.query.filter_by(user_id=user.id).first()
    if vehicle_information.status == 1:
        spot_status = Spot.query.filter_by(spot_id=vehicle_information.spot).first()
        contents = {'status': vehicle_information.status, 'spot': vehicle_information.spot,
                    'start_time': spot_status.start_time,
                    'rate': spot_status.rate, 'spot_status': spot_status.status,'balance':account.deposit}
        return app.response_class(json.dumps(contents), content_type='application/json')
    else:
        contents = {'status': vehicle_information.status,'balance':account.deposit}
        return app.response_class(json.dumps(contents), content_type='application/json')
    # except Exception as e:
    #     contents = {'error': str(e)}
    #     return app.response_class(contents, content_type='application/json', status=404)


@app.route("/history")
def get_spot_history():
    #try:
    user_email = str(current_user)
    user_info = User.query.filter_by(email=user_email).first()
    user_role = db.session.query(roles_users).filter_by(user_id=user_info.id).first()
    if user_role.role_id == 2:
        history_record = Record.query.all()
    else:
        history_record = Record.query.filter_by(user_id=user_info.id).all()
    contents = {}
    print(history_record)
    for i in range(len(history_record)):
        column = {'id': history_record[i].id, 'user_id': history_record[i].user_id,
                  'spot': history_record[i].spot, 'plate': history_record[i].plate,
                  'start_time': history_record[i].start,
                  'end_time': history_record[i].end, 'rate': history_record[i].rate}
        contents[str(i)]=column
    return app.response_class(json.dumps(contents), content_type='application/json')
    #except Exception as e:
     #   contents = {"Error": str(e)}
      #  return app.response_class(json.dumps(contents), content_type='application/json', status=404)

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
                display("Welcome in!")
                in_plate = str(plate_recognize(camera))
                if in_plate == "error":
                    continue
                camera.stop_preview()
                in_vehicle = Vehicle.query.filter_by(plate=in_plate).first()
                if in_vehicle is None:
                    display("No permit in!")
                else:
                    spot = search_spot()
                    if in_plate == "EA7THE":
                        send_data(1)
                    if spot != -1:
                        in_spot = Spot.query.filter_by(spot_id=spot).first()
                        text = "Welcome in!\n" + "Spot:" + str(in_spot.spot_id)
                        #sendSMS(text)
                        display(text)
                        set_in_servo(07)
                        in_vehicle.status = 1
                        in_vehicle.spot = spot
                        
                        in_spot.start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print (in_vehicle.status, in_vehicle.spot, in_spot.start_time, in_spot.rate)
                        in_spot.rate = global_rate
                        
                        db.session.commit()
                        while grovepi.analogRead(light_sensor_in) < threshold_light:
                            time.sleep(2)
                        time.sleep(2)
                        set_out_servo(07)
                        display("Ready for service")
                    else:
                        display("No vacant spot!")
            if exit_value < threshold_light:
                print("23123131")
                display("Welcome out!")
                out_plate = str(plate_recognize(camera))
                if out_plate == "error":
                    continue
                camera.stop_preview()
                out_vehicle = Vehicle.query.filter_by(plate=out_plate).first()
                out_spot = Spot.query.filter_by(spot_id=out_vehicle.spot).first()
                out_account = Account.query.filter_by(user_id=out_vehicle.user_id).first()
                end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                start_time = datetime.datetime.strptime(out_spot.start_time, '%Y-%m-%d %H:%M:%S')
                fee = (end_time - start_time).total_seconds() * out_spot.rate
                client_fee.connect(host, 1883, 60)
                client_fee.publish(topic_fee, json.dumps({'Fee':fee}))
                print(fee,out_account.deposit)
                if out_account.deposit < fee:
                    text = "No sufficient fund!"
                    #sendSMS(text + " Please refill account!")
                    display(text)
                else:
                    if out_plate == "EA7THE":
                        send_data(0)
                    text = "See you!\n" + "Plate:" + str(out_vehicle.plate)
                    sendSMS(text+"\nFee:" + str(fee))
                    display(text)
                    out_account.deposit -= fee
                    new_record = Record(user_id=out_vehicle.user_id, spot=out_vehicle.spot, plate=out_vehicle.plate,
                                        start=out_spot.start_time, end=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rate=out_spot.rate)
                    db.session.add(new_record)
                    print(fee,out_account.deposit)
                    out_vehicle.status = 0
                    out_vehicle.spot = 0
                    out_spot.start_time = None
                    db.session.commit()
                    while grovepi.analogRead(light_sensor_out) < threshold_light:
                        time.sleep(2)
                    display("Ready for service")
            time.sleep(2)
        except Exception as e:
            continue
    return 


def camera_capture(camera):
    camera.start_preview()
    file_name = time.asctime(time.localtime(time.time()))
    camera.capture('image/' + file_name + '.jpg')
    return file_name


def plate_recognize(camera):
    try:
    # Sample image file is available at http://plates.openalpr.com/ea7the.jpg
        file_name = camera_capture(camera)
        image_path = os.path.abspath(os.path.dirname(__file__)) + '/image/' + file_name + '.jpg'
        secret_key = 'sk_2a656f671be8995a57765172'
        with open(image_path, 'rb') as image_file:
            img_base64 = base64.b64encode(image_file.read())
        url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s' % secret_key
        r = requests.post(url, data=img_base64)
        r = r.json()
        plate_result = r["results"][0]["plate"]
        return plate_result
    except Exception as e:
        time.sleep(5)
        return "error"

def send_data(value):
    http = urllib3.PoolManager()
    r = http.request('GET', 'http://10.16.29.212:1880/turnOn?value='+str(value))

def display(word):
    grove_rgb_lcd.setText(word)
    grove_rgb_lcd.setRGB(250,128,114)


def search_spot():
    if Spot.query.filter_by(spot_id=1).first().status == 0:
        return 1
    if Spot.query.filter_by(spot_id=2).first().status == 0:
        return 2
    if Spot.query.filter_by(spot_id=3).first().status == 0:
        return 3
    return -1

def set_in_servo(port):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(port, GPIO.OUT)
    p = GPIO.PWM(port, 50)
    p.start(0)
    GPIO.output(port, True)
    p.ChangeDutyCycle(5)
    time.sleep(0.235)
    GPIO.output(port, False)
    p.ChangeDutyCycle(0)
    p.stop()
    GPIO.cleanup()

def set_out_servo(port):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(port, GPIO.OUT)
    p = GPIO.PWM(port, 50)
    p.start(0)
    GPIO.output(port, True)
    p.ChangeDutyCycle(8)
    time.sleep(0.243)
    GPIO.output(port, False)
    p.ChangeDutyCycle(0)
    p.stop()
    GPIO.cleanup()


def sendSMS(text):
    client = nexmo.Client(key='1ad97b4e', secret='jCtDbYq8ylyjeUzy')
    
    
    client.send_message({
    'from': '12532387938',
    'to': '12538837083',
    'text': text,
    })

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
admin.add_view(CustomView(name="Report", endpoint='custom', menu_icon_type='fa',
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
    
@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    p = Process(target=check_entrance_status)
    #p = Process(target=f)
    p.start()
    
    
    
    
    
    app.run(host='0.0.0.0',debug=False)
    # Build a sample db on the fly, if one does not exist yet.

