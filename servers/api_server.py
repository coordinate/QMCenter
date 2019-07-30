import codecs

from flask import Flask, jsonify, send_from_directory
import random
import numpy as np
import requests

app = Flask(__name__)


tasks = {
        'id': 1,
        'title': 'magnet points',
        # 'points': [[2, 1, 4], [4, 5, 5], [7, 5, 4.2], [6, 4, 5.1], [9, 6, 5]],
        'points_x': [2, 4, 7, 6, 9],
        'points_y': [1, 5, 5, 4, 6],
        'done': False}


@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/download', methods=['POST'])
def index():
    response = send_from_directory(directory='D:\\a.bulygin\QMCenter\data', filename='mag_track.magnete')
    return response


# @app.route('/download')
# def root():
#     return app.send_static_file('data\\mag_track.magnete')


if __name__ == '__main__':
    app.run(debug=True)
