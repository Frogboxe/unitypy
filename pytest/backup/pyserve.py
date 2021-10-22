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


class Client:
    """
    Client that forms and control the connection and communication
    to and from the Server

    self.socket: socket.socket
    """
    def __init__(self, ip: Address):
        self.socket = sockets.socket()
        self.ip = ip

    def __del__(self):
        self.close()

    def start(self):
        "opens up the client's connection to the specified server"
        self.connect()

    def connect(self):
        self.socket.connect(self.ip.astuple())

    def send(self, data: dict):
        msgsend(self.socket, data)

    def recv(self) -> dict:
        return msgrecv(self.socket)

    def close(self):
        self.socket.close()

class TestServer(Server):
    ip: Address=Address()
    def operate(self):
        self.accept_clients()
        networklog(f"Starting host service on {self.ip}")
        try:
            self._operate()
        finally:
            self.socket.close()

    def _operate(self):
        while True:
            cmd = self.queue.dequeue()
            if cmd is not None:
                self.handle_request(*cmd)

    def handle_request(self, addr: Address, request: dict) -> bool:
        if not request:
            return False
        if "TEST_ID" in request:
            networklog(request["TEST_ID"])
            self.clients[addr].send({"DONE": True})
            return True
        elif "TEST_ID" not in request:
            networklog("Nothing")
            self.clients[addr].send({"DONE": False})

def serv():
    server = Server(IP, 5.0)
    server.accept_clients()
    i = 0
    while True:
        server.send_all({"time": time.time(), "id": i})
        if i % 100 == 0:
            networklog(f"Server alive at {i}")
        i += 1
        time.sleep(0.005)

def cli(sampler=0):
    time.sleep(1)
    c = Client(IP)
    c.connect()
    while True:
        packet = c.recv()
        networklog("{}:\t{}\t\t({})".format(sampler, packet["time"], packet["id"]))
    c.close()

def self_test():
    threads = [call(serv)]
    for i in range(3):
        threads.append(call(lambda: cli(i)))
    try:
        while True:
            try:
                time.sleep(0.05)
            except KeyboardInterrupt:
                break
    except Exception:
        raise
    finally:
        for t in threads:
            t.join()

def server_test():
    t = call(serv)
    t.join()

def client_test():
    t = call(cli)
    t.join()

def cs_test():
    server = TestServer(IP)
    server.operate()



parser = argh.ArghParser()
parser.add_commands([self_test, server_test, client_test, cs_test])

if __name__ == "__main__":
    IP = Address("127.0.0.1", 31775)
    LM = logdumps.initialise_log_manager()
    LM.add_file(logdumps.create_log_target("networklog", "c:/workshop/tools/networklog.txt"))
    try:
        networklog = LM.create_log({"networklog", "stdout"}, defaultKwargs={"flush": True})
        parser.dispatch()
    finally:
        LM.close()
    
    
















































































    
