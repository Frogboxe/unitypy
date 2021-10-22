"""

@ipv4: (str, int) WHERE str is ip address AND int is port number

LegacyJsonIP packet:
    {number of bytes}
    {json}
Example:
    2
    {}
Example:
    14
    {"test":False}

NewJsonIP packet (ZERO_STRING = "0"; DENARY_MAX_LENGTH_DIGITS = 12):
    {number of bytes}
    {json}
Example:
    000000000010
    {"test":0}
Example:
    000000000012
    {"test":"0"}
"""

import socket
import json

import threading
import time

import random

from logger import *

ENCODING = "utf-8"
ZERO_STRING = "0"
DENARY_MAX_LENGTH_DIGITS = 12

def call(func: type(lambda:0)) -> threading.Thread: # type(lambda:0) shows up as "function" in quickview
    "calls function in a subthread and returns that thread"
    t = threading.Thread(target=func)
    t.start()
    return t

# NOTICE: jsonsend and jsonrecv are directly derived from
# the functions _recv and _send in jsonsocket.py, created by
# mdebbar. The original functions do not, however, work as-is.
def jsonsend(socket: socket.socket, data: dict):
    "send a json packet over the given socket"
    """
    Note: the newline terminates the bytes count AND is
    not included in the bytes count figure.
    """
    serialised = json.dumps(data)
    msg = bytes(str(len(serialised)).rjust(DENARY_MAX_LENGTH_DIGITS, ZERO_STRING), ENCODING)
    socket.send(msg)
    socket.sendall(bytes(serialised, encoding=ENCODING))

def jsonrecv(socket: socket.socket) -> dict:
    "recieve one json packet over the given socket"
    """
    jsonrecv recieves a jsonsend formatted packet from the sender.

    See jsonsend for more details.
    """
    # read and interpret the length of the jsonsend packet
    length = str(socket.recv(DENARY_MAX_LENGTH_DIGITS), ENCODING)
    if length == "":
        return None
    length = int(length)
    view = memoryview(bytearray(length))
    offset = 0
    while length - offset > 0:
        recvSize = socket.recv_into(view[offset::], length - offset)
        offset += recvSize
    return json.loads(view.tobytes())

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

    def __index__(self, i) -> "untyped":
        with self.lock:
            return self.list[i]

    def __repr__(self) -> str:
        return "Q{}:{}".format(self.i, self.list)

    def dequeue(self) -> "untyped":
        with self.lock:
            if self.i >= len(self.list):
                return
            element = self.list[self.i]
            self.i += 1
        return element

    def enqueue(self, element: "untyped"):
        with self.lock:
            self.list.append(element)

class Connection:
    """
    [09/12/17]
    Represents a connection between client and a server. This
    is universal and used by both client and server to communicate

    self.conn: socket.socket
    self.addr: str, int # where str is IPv4 address and int is port number
    """
    def __init__(self, data: ("socket.socket", "@ipv4"), queue: Queue):
        self.closed = False
        self.conn, self.addr = data
        self.queue = queue

    def __del__(self):
        self.close()

    def send(self, data: dict):
        "send json packet"
        if self.closed:
            return False
        jsonsend(self.conn, data)
        return True

    def close(self):
        self.closed = True
        self.conn.close()

    def recv(self) -> bool:
        "returns success flag. data stored in the Connection's queue"
        if self.closed:
            return False
        try:
            data = jsonrecv(self.conn)
        except (ConnectionAbortedError, ConnectionResetError) as e:
            self.queue.enqueue((self.addr, None))
            return False
        if not data:
            self.queue.enqueue((self.addr, None))
            return False
        self.queue.enqueue((self.addr, data))
        return True

    def recv_repeat(self):
        "recv but until connection closed. thread always listening"
        while True:
            if not self.recv():
                self.close()
                return

class Server:
    "ip: host ip address; clients: max allowed clients"
    """
    Server that forms and controls connection and communication between
    itself and the client(s)

    self.clients: dict
    self.socket: socket.socket
    """
    def __init__(self, ip: "@ipv4", timeout: float=10.):
        self.socket = socket.socket()
        self.socket.bind(ip)
        self.socket.listen()
        self.socket.settimeout(timeout)
        self.clientLock = threading.Lock()
        self.clients = {}
        self.queue = Queue()
        self.accpThread = threading.Thread
        self.recvThreads = []

    def __del__(self):
        try:
            for thread in self.recvThreads:
                thread.join()
            self.accpThread.join()
        except AttributeError:
            pass # if the threads aren't visible here, then they will
                 # be garbage collected anyway.

    def __str__(self):
        return str(self.queue)

    def start(self):
        "starts accepting and processing clients"
        self.accept_clients()

    def accept_clients(self):
        "opens a new thread constantly accepting new clients"
        self.accpThread = call(lambda: self.grab_clients())

    def send_all(self, data: dict):
        "sends given json packet to every open Connection"
        with self.clientLock:
            for client in self.clients.values():
                client.send(data)

    def grab_clients(self):
        "constantly accept new clients and add them to the active client list"
        while True:
            try:
                conn = Connection(self.socket.accept(), self.queue)
                with self.clientLock:
                    self.clients[conn.addr] = conn
                t = call(lambda: conn.recv_repeat())
                self.recvThreads.append(t)
            except socket.timeout:
                pass


class Client:
    """
    Client that forms and control the connection and communication
    to and from the Server

    self.socket: socket.socket
    """
    def __init__(self, ip: "@ipv4"):
        self.socket = socket.socket()
        self.ip = ip

    def __del__(self):
        self.close()

    def start(self):
        "opens up the client's connection to the specified server"
        self.connect()

    def connect(self):
        self.socket.connect(self.ip)

    def send(self, data: dict):
        jsonsend(self.socket, data)

    def recv(self) -> dict:
        return jsonrecv(self.socket)

    def close(self):
        self.socket.close()


def serv():
    s = Server(("192.168.0.28", 10578), 5.0)
    s.accept_clients()
    i = 0
    while True:
        i += 1
        time.sleep(0.1)
        s.send_all({"time": time.time(), "id": i})

def cli(sampler=0):
    time.sleep(1)
    c = Client(("81.100.96.128", 10578))
    c.connect()
    while True:
        packet = c.recv()
        print("{}:\t{}\t\t({})".format(sampler, str(time.time() - packet["time"]).ljust(24, ZERO_STRING), packet["id"]))
    c.close()


serv()


ls = []

mt = call(serv)
for i in range(4):
    ls.append(call(lambda: cli(i)))

for t in ls:
    t.join()

mt.join()
























