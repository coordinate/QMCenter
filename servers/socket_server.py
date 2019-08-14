import socket
import random
# import msg_pb2
import websockets
import asyncio
import json
import time

from ctypes import windll, Structure, c_long, byref


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


def queryMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return json.dumps({"x": pt.x, "y": pt.y})

# # Задаем адрес сервера
# SERVER_ADDRESS = ('', 8686)
#
# # Настраиваем сокет
# server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_socket.bind(SERVER_ADDRESS)
# server_socket.listen(10)
# print('server is running, please, press ctrl+c to stop')
#
#
# message = msg_pb2.msg()
# connection, address = server_socket.accept()
# print("new connection from {address}".format(address=address))
#
#
# # Слушаем запросы
# while True:
#
#     data_json = connection.recv(10)
#     print(str(data_json))
#
#     value = random.randint(10, 100)
#     message.value = value
#     print(value)
#
#     s = message.SerializeToString()
#     connection.send(s)


def foo():
    for i in range(1000000):
        yield i


i = iter(foo())

loop = asyncio.get_event_loop()

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


def crate_json():
    data = {'GPStime': {'type': 'int_32', 'value': random.randint(1, 50)},
            'freq': {'type': 'int_32', 'value': random.randint(100, 250)},
            'time': {'type': 'int_32', 'value': next(i)}}

    return json.dumps(data)


async def hello(websocket, path):
    # name = await websocket.recv()
    # print(name)
    while True:
        data = read()
        # data_json = queryMousePosition()
        await websocket.send(data)
        time.sleep(0.05)

start_server = websockets.serve(hello, "", 8765)

loop.run_until_complete(start_server)
loop.run_forever()
