import json
import os

from PyQt5 import QtCore, QtWebSockets, QtNetwork, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction
from PyQt5.QtCore import QUrl, QTimer

data_json = {'jsons': {}}
with open('../workdocs/data/raw_magnet_data.txt', 'r') as file:
    a = file.readlines()


def read_lines():
    for s in a:
        yield s


it = iter(read_lines())


def read():
    for i in range(100):
        n = next(it).split()
        data_json['jsons']['json{}'.format(i)] = [int(n[1]), float(n[3]), int(n[5]), int(n[7]), int(n[9]),
                                                  int(n[11]), int(n[13]), int(n[15])]     # (time, freq, sig1, sig2, ts, isitemp, dc, temp)

    return json.dumps(data_json)


def create_workdir(folder):
    directory = {}
    path = 'D:/a.bulygin/QMCenter/workdocs/{}/'.format(folder)
    if not os.path.isdir(path):
        return json.dumps({'directory': 0})
    lst = os.listdir(path)
    for l in lst:
        directory[l] = {'type': 'folder' if os.path.isdir(path + l) else 'file',
                        'size': round(os.path.getsize('{}{}'.format(path, l))/1024, 2),
                        'changed_date': os.path.getctime('{}{}'.format(path, l)),
                        }
        # directory[l] = [round(os.path.getsize('{}{}'.format(path, l))/1024, 2), datetime.datetime.fromtimestamp(os.path.getctime('{}{}'.format(path, l))).strftime('%d/%m/%y')]
    path_trecked_folder = 'D:/a.bulygin/QMCenter/workdocs/start_folder/tracked_folder/'
    lst_tracked_folder = os.listdir(path_trecked_folder)
    return json.dumps({'directory': directory, 'tracked_folder': lst_tracked_folder})


class MyServer(QtCore.QObject):
    def __init__(self, parent):
        super(QtCore.QObject, self).__init__(parent)
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.send_data)
        self.clients = []
        print("server name: {}".format(parent.serverName()))
        self.server = QtWebSockets.QWebSocketServer(parent.serverName(), parent.secureMode(), parent)
        if self.server.listen(QtNetwork.QHostAddress('127.0.0.1'), 8765):
            print('Listening: {}:{}:{}'.format(
                self.server.serverName(), self.server.serverAddress().toString(),
                str(self.server.serverPort())))
        else:
            print('error')
        self.server.acceptError.connect(self.onAcceptError)
        self.server.newConnection.connect(self.onNewConnection)
        self.clientConnection = None
        print(self.server.isListening())

    def onAcceptError(accept_error):
        print("Accept Error: {}".format(accept_error))

    def onNewConnection(self):
        print("onNewConnection")
        self.clientConnection = self.server.nextPendingConnection()
        self.clientConnection.textMessageReceived.connect(self.processTextMessage)

        self.clientConnection.textFrameReceived.connect(self.processTextFrame)

        self.clientConnection.binaryMessageReceived.connect(self.processBinaryMessage)
        self.clientConnection.disconnected.connect(self.socketDisconnected)

        print("newClient", self.clientConnection)
        self.clients.append(self.clientConnection)
        self.timer.start()

    def processTextFrame(self, frame, is_last_frame):
        print("in processTextFrame")
        print("\tFrame: {} ; is_last_frame: {}".format(frame, is_last_frame))

    def send_data(self):
        data = read()
        # data_json = queryMousePosition()
        if len(self.clients) > 0:
            self.clients[0].sendTextMessage(data)

    def processTextMessage(self, message):
        print("processTextMessage - message: {}".format(message))
        jsn = json.loads(message)
        if self.clientConnection:
            if 'folder' in jsn:
                self.clients[0].sendTextMessage(create_workdir(jsn['folder']))

        # for client in self.clients:
            #     # if client!= self.clientConnection:
            #     client.sendTextMessage(message)
            # self.clientConnection.sendTextMessage(message)

    def processBinaryMessage(self, message):
        print("b:",message)
        if self.clientConnection:
            self.clientConnection.sendBinaryMessage(message)

    def socketDisconnected(self):
        print("socketDisconnected")
        if self.clientConnection:
            self.clients.remove(self.clientConnection)
            self.clientConnection.deleteLater()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    serverObject = QtWebSockets.QWebSocketServer('My Socket', QtWebSockets.QWebSocketServer.NonSecureMode)
    server = MyServer(serverObject)
    serverObject.closed.connect(app.quit)
    app.exec_()