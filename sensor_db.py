from flask import Flask, Response, jsonify
import argparse
import random
import time
import sqlite_utils
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from io import StringIO
import csv
import socket
import json, requests, os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging
logging.getLogger("werkzeug").disabled = True


import encryptionCompression as ec
aes_key = ec.load_aes_key_from_file('keys/aes_key.bin')

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
node_address = "https://127.0.0.1:33696/register"
headers = {
            'Content-Type': 'application/json'
            }
from flask_talisman import Talisman
csp = {
    'default-src': [
        '\'self\'',
        '*.scss.tcd.ie'
    ]
}

app = Flask(__name__)
talisman = Talisman(app, content_security_policy=csp, strict_transport_security=True)

parser = argparse.ArgumentParser(description='Run sensor')
parser.add_argument('--port', type=str, help='Run on which port')
parser.add_argument('--sensor', type=str, help='Run on which port')

args = parser.parse_args()

if args.sensor == "temp":
    minval = 0  # Celsius
    maxval = 30
    value = "Temperature"
    unit = "Celsius"

elif args.sensor == "rain":
    minval = 0  #mm of rainfall
    maxval = 10
    value = "Rainfall"
    unit = "mm"

elif args.sensor == "dist_front":
    minval = 1  #mm of rainfall
    maxval = 10
    value = "Ultrasonic_Distance_Sensor_Front"
    unit = "m"

elif args.sensor == "dist_rear":
    minval = 1  #mm of rainfall
    maxval = 20
    value = "Ultrasonic_Distance_Sensor_Rear"
    unit = "m"

elif args.sensor == "dist_left":
    minval = 1  #mm of rainfall
    maxval = 8
    value = "Ultrasonic_Distance_Sensor_Left"
    unit = "m"   

elif args.sensor == "dist_right":
    minval = 1  #mm of rainfall
    maxval = 9
    value = "Ultrasonic_Distance_Sensor_Right"
    unit = "m"

elif args.sensor == "light":
    minval = 20  #mm of rainfall
    maxval = 100
    value = "Light_Sensor"
    unit = "%"

elif args.sensor == "gps_lat":
    minval = 53.349804  #mm of rainfall
    maxval = 53.359804
    value = "Latitude"
    unit = ""

elif args.sensor == "gps_long":
    minval = -6.260310  #mm of rainfall
    maxval = -6.250310
    value = "Longitude"
    unit = ""

elif args.sensor == "wind":
    minval = 2  #mm of rainfall
    maxval = 20
    value = "Wind_Sensor"
    unit = "m/s"
elif args.sensor == "speed":
    minval = 20  #mm of rainfall
    maxval = 80
    value = "Speed"
    unit = "km/hr"
elif args.sensor == "fuel":
    minval = 10  #mm of rainfall
    maxval = 20
    value = "Fuel"
    unit = "L"
elif args.sensor == "RPM":
    minval = 10  #mm of rainfall
    maxval = 20
    value = "Revs_per_min"
    unit = "rpm"
elif args.sensor == "inttemp":
    minval = 30  #mm of rainfall
    maxval = 50
    value = "Internal_temp"
    unit = "Celsius"
else:
    print("Sensor not recognized")
    exit()

database_path = "data/sensor.db"

@app.route('/checkalive', methods=['GET'])
def check_alive():
    print("Alive")
    # print(hostname, IPAddr)
    # return jsonify({'message': '{} is alive!'.format("https://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie")}), 200
    return jsonify({'message': '{} sensor is alive!'.format(value)}), 200

def broadcast_alive():
    json_payload = {"sensor_name": value, "port": args.port}
    data_payload = json.dumps(json_payload)
    json_data_bytes = data_payload.encode('utf-8')
    json_data_bytes = ec.encrypt_message(json_data_bytes, aes_key)
    
    try:
        response = requests.post(node_address, headers=headers, data=json_data_bytes, timeout=1, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.RequestException as e:
        print("Unable to register with server")

def generate_sensor_data():
    if value == "Latitude" or value == "Longitude":
        data = (minval + maxval) / 2
        random_variation = random.uniform(-0.0001, 0.0001)
        data = data + random_variation
        # Ensure the temperature stays within the specified range
        data = max(minval, min(data, maxval))
        return round(data, 6)

    data = (minval + maxval) / 2
    random_variation = random.uniform(-2, 2)
    data = data + random_variation
    # Ensure the temperature stays within the specified range
    data = max(minval, min(data, maxval))
    return round(data, 2)

# Function to insert temperature data into the SQLite database
def insert_sensor_data():
    # print("creating db")

    # Connect to the SQLite database
    db = sqlite_utils.Database(database_path)

    # Create a table if it doesn't exist
    if value not in db.table_names():
        db[value].create({
            "timestamp": int,
            value: float
        })
    # Generate data
    insert_data = generate_sensor_data()
    # Insert data into the database
    db[value].insert({
        "timestamp": int(time.time()),
        value: insert_data
    })
    row_count = db.execute('SELECT COUNT(*) FROM {}'.format(value)).fetchone()[0]
    rows_to_delete = row_count - 1000
    if rows_to_delete > 0:
        try:
            db.execute('DELETE FROM {} ORDER BY ROWID ASC LIMIT 1'.format(value))
            db.conn.commit()
        except Exception as e:
            print(f"Error: {e}")
    # print("Added to db")

@app.route('/sensor_data/<float:duration_hours>', methods=['GET'])
def get_sensor_data(duration_hours):
    # Connect to the SQLite database
    db = sqlite_utils.Database(database_path)

    # Retrieve the first 50 rows from the "temperature_data" table
    # result = db.execute('SELECT * FROM {}'.format(value)).fetchall()
    result = db.execute('SELECT * FROM {} ORDER BY timestamp DESC LIMIT {}'.format(value, duration_hours*60*60/5)).fetchall()
    csv_data = StringIO(newline='')
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(['Timestamp(Epoch)', "{}({})".format(value,unit)])
    csv_writer.writerows(result)
    # print(csv_data)

    headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename={}.csv'.format(value)
    }
    return Response(csv_data.getvalue(), headers=headers)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=insert_sensor_data, trigger="interval", seconds=5)
    scheduler.add_job(func=broadcast_alive, trigger="interval", seconds=10)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
    app.run(host="localhost", port=args.port, ssl_context='adhoc')