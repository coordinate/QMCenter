import codecs
import json

from flask import Flask, jsonify, send_from_directory, request
import random
import numpy as np
import requests

app = Flask(__name__)


data = {
        'P': [10, 10, 250],
        'D': [1, 2, 3],
        'Po': {
            'V': [123, 50, 200],
            'C': [321, 0, 400],
            'Te': [22, -10, 100]},
        'Par': ['Sota']
    }


device = {
        'Parameter 1': [154.7, 100.0, 250.0],
        'DSP Module': [1, 2, 3],
        'Power Module': {
            'Voltage': [123, 50, 200],
            'Current': [321, 0, 400],
            'Temperature': [22, -10, 100]},
        'Parameter 2': ['Some data', '', '']
    }


@app.route('/config', methods=['GET'])
def get_tasks():
    return jsonify({'data': data})


@app.route('/device', methods=['GET'])
def get_update():
    with open('../workdocs/config_device.json', 'r') as file:
        device = json.load(file)
    return jsonify(device)


@app.route('/download', methods=['POST'])
def index():
    response = send_from_directory(directory='D:\\a.bulygin\QMCenter\data', filename='mag_track.magnete')
    return response


@app.route('/api/add_message/<uuid>', methods=['POST'])
def add_message(uuid):
    content = request.json
    with open('../workdocs/config_{}.json'.format(uuid), 'w') as file:
        json.dump(content, file, indent=4, sort_keys=True)
    return jsonify({"uuid": uuid})


# @app.route('/download')
# def root():
#     return app.send_static_file('data\\mag_track.magnete')


if __name__ == '__main__':
    app.run(debug=True)
