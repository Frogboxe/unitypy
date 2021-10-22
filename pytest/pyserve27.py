



import socket as sockets
import threading
import time
import traceback
import struct

import msgpack

from pyserveconst import PY_CONNECT_ADDR, PY_CONNECT_PORT, PY_CONNECT_FUNCTION_ID, PY_CONNECT_ARGS_ID, PY_CONNECT_RETURN

CALL = '& "C:\\Users\\frogb\\AppData\\Local\\Programs\\Python\\Python27\\python.exe" c:/workshop/tools/pyserve27.py'

INFO_BYTES = 4

def call(func):
    "calls function in a subthread and returns that thread"
    "thread is a daemon by default"
    t = threading.Thread(target=func)
    t.setDaemon(True)
    t.start()
    return t

def msgsend(socket, data):
    serialised = msgpack.dumps(data)
    packet = struct.pack(">L", len(serialised)) + serialised
    socket.send(packet)

def msgrecv(socket):
    length = struct.unpack(">L", socket.recv(INFO_BYTES))[0]
    raw = socket.recv(length)
    data = msgpack.loads(raw)
    return data

class Queue:
    "thread safe queue (made of requests system)"
    """
    Thread-safe single-element-expanding queue. Queue with dequeue and enqueue.
    Random access via __index__
    """
    def __init__(self):
        self.list = []
        self.lock = threading.Lock()
        self.i = 0

    def __repr__(self):
        return "Q{}:{}".format(self.i, self.list)

    def dequeue(self):
        with self.lock:
            if self.i >= len(self.list):
                return
            element = self.list[self.i]
            self.i += 1
        return element

    def enqueue(self, element):
        with self.lock:
            self.list.append(element)

class Address:
    def __init__(self, ip, port):
        self.ip, self.port = ip, port

    def astuple(self):
        return self.ip, self.port

class Client:
    """
    Client that forms and control the connection and communication
    to and from the Server

    self.socket: socket.socket
    """
    def __init__(self, ip):
        self.socket = sockets.socket()
        self.ip = ip

    def __del__(self):
        self.close()

    def start(self):
        "opens up the client's connection to the specified server"
        self.connect()

    def connect(self):
        self.socket.connect(self.ip.astuple())

    def send(self, data):
        msgsend(self.socket, data)

    def recv(self):
        return msgrecv(self.socket)

    def close(self):
        self.socket.close()


class PyClient:
    def __init__(self):
        self.client = Client(Address(PY_CONNECT_ADDR, PY_CONNECT_PORT))
        self.client.connect()
        self.queue = Queue()
        self.lock = threading.Lock()
    
    def remote_call(self, f, *args):
        self.client.send({PY_CONNECT_FUNCTION_ID: f, PY_CONNECT_ARGS_ID: args})
        print("waiting")
        return self.client.recv()[PY_CONNECT_RETURN]


def main():
    pc = PyClient()
    print(pc.remote_call("echo", "testing text"))

if __name__ == "__main__":
    IP = Address("127.0.0.1", 31775)
    main()
    
    


##s = "C:\workshop\pytest\pyserve27.py"
##py2 = "C:\Users\frogb\AppData\Local\Programs\Python\Python27"



