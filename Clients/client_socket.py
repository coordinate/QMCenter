import json

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtCore import QTimer, Qt, pyqtSignal


class Client(QtCore.QObject):
    relative_time = -1
    signal_data = pyqtSignal(object, object, object, object, object, object, object, object)
    signal_connection = pyqtSignal()
    signal_disconnect = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.error)
        self.client.pong.connect(self.onPong)

    def do_ping(self):
        print("client: do_ping")
        self.client.ping(b"foo")

    def send_message(self):
        print("client: send_message")
        self.client.sendTextMessage("hello")

    def onPong(self, elapsedTime, payload):
        print("onPong - time: {} ; payload: {}".format(elapsedTime, payload))

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.client.errorString())

    def close(self):
        self.client.close()
        # self.client.disconnect()
        self.signal_disconnect.emit()

    def connect(self):
        self.client.open(QtCore.QUrl("ws://localhost:8765"))
        self.signal_connection.emit()
        self.client.sendTextMessage("test message")
        self.client.textMessageReceived.connect(self.decoding_json)

    def decoding_json(self, jsn):
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
            self.signal_data.emit(arr_freq, arr_time, arr_sig1, arr_sig2,
                                  arr_ts, arr_isitemp, arr_dc, temp)
