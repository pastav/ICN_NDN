# SC-Project-3
SC-Project-3

Run Centralized Server using:
python3 central.py

Run NDN Server using:
python3 server.py --name <INSERT_NAME>

Run a Sensor which produces data:
python3 sensor_db.py --sensor light --port 33707

Use the sensor names as given in senson_db.py
Use ports 33600-33700, 33696 and 33700 are being used by NDN server and Central.py respectively

Run a Device which consumes data:
python3 device.py --interest Light_Sensor --name pikachu --data Light_Sensor --duration 0.1
