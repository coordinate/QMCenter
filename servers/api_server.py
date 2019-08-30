import json

from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__)
# l = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
# ALLOWED_EXTENSIONS = set(l)
# UPLOAD_FOLDER = "D:/a.bulygin/QMCenter/workdocs/server"
# app.secret_key = "secret key"
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['update_file']
        with open('D:\\a.bulygin\\QMCenter\\workdocs\\server\\'+f.filename, 'wb') as file:
            file.write(f.read())
        return jsonify({'success': True})


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

update = {
        'HW_PCB_ver': [1.0],
        'HW_Assembly_ver': [1.0],
        'Firmware': [1.0],
        'Software': [1.0]
    }


@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({'data': data})


@app.route('/update', methods=['GET'])
def get_update():
    return jsonify({'update': update})


@app.route('/device', methods=['GET'])
def get_device():
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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000', debug=True)
