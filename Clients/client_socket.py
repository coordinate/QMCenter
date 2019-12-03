import re
import json
import subprocess
from threading import Thread

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtCore import QTimer, pyqtSignal, QRegExp


class Client(QtCore.QObject):
    relative_time = -1
    signal_stream_data = pyqtSignal(object, object, object, object, object, object, object, object)
    signal_directory_data = pyqtSignal(object)
    signal_connection = pyqtSignal()
    signal_autoconnection = pyqtSignal()
    signal_disconnect = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(self.parent.server):
            self.ip = self.parent.server
        else:
            self.ip = None
        self.port = '8765'

        self.ping_server_timer = QTimer()
        self.ping_server_timer.setInterval(800)
        self.ping_server_timer.start()
        self.ping_server_timer.timeout.connect(lambda: self.ping_server())

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.error)
        self.client.textMessageReceived.connect(self.decoding_json)
        self.client.pong.connect(self.onPong)

        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

    def change_ip(self, ip):
        self.ip = ip

    def ping_server(self):  # standard (cmd) ping command
        def enqueue_output():
            cmd = "ping -w 800 -n 1 {}".format(self.ip)
            out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()
            lines = out.decode('cp866')
            try:
                lost_percent = re.findall(r'\d+%', lines)[0].split('%')[0]
                if int(lost_percent) < 50:
                    self.signal_connection.emit()
                    self.signal_autoconnection.emit()
                else:
                    self.signal_disconnect.emit()
            except IndexError:
                print('ping command is not done')
                self.signal_disconnect.emit()
        if self.ip is not None:
            t = Thread(target=enqueue_output)
            t.daemon = True  # thread dies with the program
            t.start()

    def do_ping(self):  # check is connection still alive (Qt function)
        print("client: do_ping")
        self.client.ping(b"foo")

    def send_message(self, msg):
        print("client: send_message")
        self.client.sendTextMessage(msg)

    def send_folder_name(self, folder):
        print("client: send_directory")
        folder_name = {'folder': folder}
        self.client.sendTextMessage(json.dumps(folder_name))

    def onPong(self, elapsedTime, payload):
        print("onPong - time: {} ; payload: {}".format(elapsedTime, payload))

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.client.errorString())
        if error_code != 0:
            self.signal_disconnect.emit()

    def close(self):
        self.client.close()

    def connect(self):
        self.client.open(QtCore.QUrl("ws://{}:{}".format(self.ip, self.port)))

    def decoding_json(self, jsn):
        if 'jsons' in jsn:
            dec = json.loads(jsn)
            arr_time = []
            arr_freq = []
            arr_sig1 = []
            arr_sig2 = []
            arr_ts = []
            arr_isitemp = []
            arr_dc = []

            for time, freq, sig1, sig2, ts, isitemp, dc, temp in dec['jsons'].values():
                Client.relative_time += 1
                arr_time.append(Client.relative_time)
                arr_freq.append(freq)
                arr_sig1.append(sig1)
                arr_sig2.append(sig2)
                arr_ts.append(ts)
                arr_isitemp.append(isitemp)
                arr_dc.append(dc)

            # print('time', arr_time, '\n', 'freq', arr_freq)
            if len(arr_time):
                self.signal_stream_data.emit(arr_freq, arr_time, arr_sig1, arr_sig2,
                                      arr_ts, arr_isitemp, arr_dc, temp)

        elif 'directory' in jsn:
            self.signal_directory_data.emit(jsn)
