import json
import os
import datetime
import shutil

from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__)
# l = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
# ALLOWED_EXTENSIONS = set(l)
# UPLOAD_FOLDER = "D:/a.bulygin/QMCenter/workdocs/server"
# app.secret_key = "secret key"
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# config tab, read btn [get(read) config file]
device = {
        'Parameter 1': [154.7, 100.0, 250.0],
        'DSP Module': [1, 2, 3],
        'Power Module': {
            'Voltage': [123, 50, 200],
            'Current': [321, 0, 400],
            'Temperature': [22, -10, 100]},
        'Parameter 2': ['Some data', '', '']
    }


@app.route('/device', methods=['GET'])
def get_device():
    with open('../workdocs/config_device.json', 'r') as file:
        device = json.load(file)
    return jsonify(device)


# config tab, write btn [post(write) new config file]
@app.route('/api/add_message/<uuid>', methods=['POST'])
def add_message(uuid):
    content = request.json
    with open('../workdocs/config_{}.json'.format(uuid), 'w') as file:
        json.dump(content, file, indent=4, sort_keys=True)
    return jsonify({"uuid": uuid})


update = {
        'HW_PCB_ver': [1.0],
        'HW_Assembly_ver': [1.0],
        'Firmware': [1.0],
        'Software': [1.0]
    }


# update tab [get(*read) update info] *automatically
@app.route('/spec_update', methods=['GET'])
def get_update():
    return jsonify({'update': update})


# update tab, wizard upload btn [post(upload) update file]
@app.route('/update', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['update_file']
        with open('D:\\a.bulygin\\QMCenter\\workdocs\\server\\'+f.filename, 'wb') as file:
            file.write(f.read())
        return jsonify({'success': True})


# file manager tab, right arrow btn [post(upload) file to device(server)]
@app.route('/upload_file_to_device/<path:path>', methods=['POST'])
def upload_file_to_device(path):
    if request.method == 'POST':
        f = request.files['upload_file']
        with open('D:/a.bulygin/QMCenter/workdocs/{}/{}'.format(path, f.filename), 'wb') as file:
            file.write(f.read())
        return jsonify({'success': True})


# file manager tab, delete btn [delete file from device(server)]
@app.route('/data/<path:path>', methods=['DELETE'])
def delete_file_from_device(path):
    if os.path.isfile('D:/a.bulygin/QMCenter/workdocs/start_folder/{}'.format(path)):
        os.remove('D:/a.bulygin/QMCenter/workdocs/start_folder/{}'.format(path))
    else:
        shutil.rmtree('D:/a.bulygin/QMCenter/workdocs/start_folder/{}'.format(path))
    return jsonify({'success': True})


@app.route('/download', methods=['POST'])
def index():
    response = send_from_directory(directory='D:\\a.bulygin\QMCenter\data', filename='mag_track.magnete')
    return response


@app.route('/data/', methods=['GET'])
def main_folder():
    directory = []
    path = 'D:/a.bulygin/QMCenter/workdocs/start_folder/'
    lst = os.listdir(path)
    for l in lst:
        directory.append({'name': l,
                          'type': 'folder' if os.path.isdir(path + l) else 'file',
                          'size': round(os.path.getsize('{}{}'.format(path, l))/1024, 2),
                          'changed': os.path.getctime('{}{}'.format(path, l))})
    return jsonify(directory)


@app.route('/data/<path:path>', methods=['GET'])
def files_folders(path):
    directory = []
    path = 'D:/a.bulygin/QMCenter/workdocs/start_folder/{}'.format(path)
    if os.path.isfile(path):
        response = send_from_directory(directory='D:/a.bulygin/QMCenter/workdocs/start_folder', filename=os.path.basename(path))
        return response
    else:
        lst = os.listdir(path)
        for l in lst:
            directory.append({'name': l,
                              'type': 'folder' if os.path.isdir(os.path.join(path, l)) else 'file',
                              'size': round(os.path.getsize('{}'.format(os.path.join(path, l)))/1024, 2),
                              'changed': os.path.getctime('{}'.format(os.path.join(path, l)))})
        return jsonify(directory)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='9080', debug=True)
