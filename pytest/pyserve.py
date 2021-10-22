"""

"""

import socket as sockets
import threading
import time
import traceback
import argh
from dataclasses import asdict, astuple, dataclass, field

import logdumps
from pyservertools import call, msgsend, msgrecv, Queue, Convertable
from pyserveconst import PY_CONNECT_ADDR, PY_CONNECT_PORT, PY_CONNECT_FUNCTION_ID, PY_CONNECT_ARGS_ID, PY_CONNECT_RETURN, PY_CONNECT_ERROR

@dataclass(frozen=True)
class Address(Convertable):
    addr: str=field(default="127.0.0.1")
    port: int=field(default=31775)

class Connection:
    """
    [09/12/17]
    Represents a connection between client and a server. This
    is universal and used by both client and server to communicate

    self.conn: sockets.socket
    self.addr: Address
    """
    def __init__(self, connect: "connection, ip", queue: Queue):
        self.closed = False
        self.conn, self.addr = connect
        self.queue = queue

    def __del__(self):
        self.close()

    def send(self, data: dict) -> bool:
        "send json packet"
        if self.closed:
            return False
        msgsend(self.conn, data)
        return True

    def close(self):
        self.closed = True
        self.conn.close()

    def recv(self) -> bool:
        "returns success flag. data stored in the Connection's queue"
        if self.closed:
            return False
        try:
            data = msgrecv(self.conn)
        except (ConnectionAbortedError, ConnectionResetError):
            self.queue.enqueue((self.addr, None))
            return False
        if data is None:
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
    """
    Server that forms and controls connection and communication between
    itself and the client(s)

    self.clients: dict
    self.socket: socket.socket
    """
    def __init__(self, ip: Address, timeout: float=10.):
        self.address = ip
        self.socket = sockets.socket()
        self.socket.bind(ip.astuple())
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
            #self.accpThread.join()
        except AttributeError:
            pass # if the threads aren't visible here, then they will
                 # be garbage collected anyway.

    def __str__(self) -> str:
        return str(self.queue)

    def __repr__(self) -> str:
        return f"Server at {self.address} has ({len(self.clients)} clients"

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
                networklog("Found Client")
                with self.clientLock:
                    self.clients[conn.addr] = conn
                t = call(lambda: conn.recv_repeat())
                self.recvThreads.append(t)
            except sockets.timeout:
                pass

def decode_all(data: list) -> list:
    networklog(data)
    LM.flush_all()
    return [d.decode(encoding="utf-8") for d in data]

def tobytes(s: str) -> bytes:
    return bytes(s, encoding="utf-8")

def tostring(d: bytes) -> str:
    return str(d, encoding="utf-8")

def all_tostring(l: list[bytes]) -> list[str]:
    return [(str(d, encoding="utf-8") if (type(d) is bytes) else d) for d in l]

class PyServer(Server):
    def __init__(self, callMap={"print": print}):
        super().__init__(Address(PY_CONNECT_ADDR, PY_CONNECT_PORT))
        self.calls = callMap

    def handle_request(self, addr: Address, data: dict) -> bool:
        networklog("handling a request")
        networklog(addr, data)
        if data is None:
            return False
        if PY_CONNECT_FUNCTION_ID in data:
            resp = self.call_noconv(data[PY_CONNECT_FUNCTION_ID], data[PY_CONNECT_ARGS_ID])
        else:
            resp = self.call(data[tobytes(PY_CONNECT_FUNCTION_ID)], data[tobytes(PY_CONNECT_ARGS_ID)])
        
        #resp = {PY_CONNECT_ERROR: True}
        self.clients[addr].send(resp)

    def operate(self):
        while True:
            data = self.queue.dequeue()
            if data:
                networklog("handling a request")
                self.handle_request(*data)

    def call(self, func: str, args: list) -> dict:
        out = self.calls[tostring(func)](*all_tostring(args))
        return {PY_CONNECT_RETURN: out}

    def call_noconv(self, func: str, args: list) -> dict:
        out = self.calls[func](*args)
        return {PY_CONNECT_RETURN: out}


def test_server():
    calls = {
        "hello": lambda: "hello friend",
        "goodbye": lambda x: f"goodbye {x}",
        "add": lambda x, y: x + y,
        "echo": lambda x: networklog(f"said {x}")
    }
    server = PyServer(callMap=calls)
    server.accept_clients()
    server.operate()






parser = argh.ArghParser()
parser.add_commands([test_server,])

if __name__ == "__main__":
    IP = Address("127.0.0.1", 31775)
    LM = logdumps.initialise_log_manager()
    LM.add_file(logdumps.create_log_target("networklog", "c:/workshop/tools/networklog.txt"))
    networklog = LM.create_log({"networklog", "stdout"}, defaultKwargs={"flush": True})
    parser.dispatch()
    
    
















































































    
