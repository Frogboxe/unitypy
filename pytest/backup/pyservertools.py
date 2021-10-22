

import socket as sockets
import struct
import threading
from dataclasses import asdict, astuple

import msgpack

INFO_BYTES = 4

def call(func: type(lambda:0), **kwargs) -> threading.Thread: # type(lambda:0) shows up as "function" in quickview
    "calls function in a subthread and returns that thread"
    "thread is a daemon by default"
    default = {
        "daemon": True
        }
    use = default | kwargs
    t = threading.Thread(target=func, **use)
    t.start()
    return t

def msgsend(socket: sockets.socket, data: dict):
    serialised = msgpack.dumps(data)
    packet = struct.pack(">L", len(serialised)) + serialised
    socket.send(packet)

def msgrecv(socket: sockets.socket) -> dict:
    length = struct.unpack(">L", socket.recv(INFO_BYTES))[0]
    raw = socket.recv(length)
    data = msgpack.loads(raw)
    return data

class Convertable:
    def astuple(self) -> tuple:
        return astuple(self)

    def asdict(self) -> dict:
        return asdict(self)


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

    def __repr__(self) -> str:
        return "Q{}:{}".format(self.i, self.list)

    def dequeue(self) -> dict:
        with self.lock:
            if self.i >= len(self.list):
                return
            element = self.list[self.i]
            self.i += 1
        return element

    def enqueue(self, element: dict):
        with self.lock:
            self.list.append(element)


    














































































