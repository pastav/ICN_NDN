import json, requests
import atexit
import time
from flask import Flask, Response, jsonify
from flask_talisman import Talisman
import logging

import os
csp = {
    'default-src': [
        '\'self\'',
        '*.scss.tcd.ie'
    ]
}
app = Flask(__name__)
talisman = Talisman(app, content_security_policy=csp, strict_transport_security=True)
logging.basicConfig(level=logging.INFO)

data_payload = {"node_name": "please","node_address": "IPAddr","device_names": "testdev","sensor_name": "testsen","sensor_port":"1234"}
json_payload = json.dumps(data_payload)
central_url =  "https://rasp-028.berry.scss.tcd.ie:33700"
headers = {
            'Content-Type': 'application/json'
            }
import encryptionCompression as ec
from apscheduler.schedulers.background import BackgroundScheduler
aes_key = ec.load_aes_key_from_file('keys/aes_key.bin')
def callfunc():
    try:
        json_data_bytes = json_payload.encode('utf-8')
        encrypted_data = ec.encrypt_message(json_data_bytes, aes_key)
        # if response is not None:
        #     response.close()
        #     response = None
        # print(central_url+"/centralregistry")
        logging.info(f"Request being sent to {central_url}/centralregistry")
        response = requests.post(central_url+"/centralregistry", headers=headers, data=encrypted_data, timeout=5, verify=False)
        logging.info(f"Request sent to {central_url}/centralregistry")
        logging.info(f"Request data: {encrypted_data}")
        response.raise_for_status()
        return response.status_code
    except Exception as e:
        logging.error(f"Error: {e}")
        print("central server down, distributed mode enabled")


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=callfunc, trigger="interval", seconds=10)
    #--------------------------
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
    app.run(host="localhost", port=33601, ssl_context='adhoc')