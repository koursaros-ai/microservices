

from hashlib import sha1
from enum import Enum
import struct
import zmq


HOST = "127.0.0.1"
ROUTER_PORT = 49152
MIN_PORT = 49153
MAX_PORT = 65536
DIFF = MAX_PORT - MIN_PORT
FLASK_PORT = 5000
POLL_TIMEOUT = 1000


class Command(Enum):
    SEND = b'0'
    STATUS = b'1'


class Route(Enum):
    IN = b'0'
    OUT = b'1'
    CTRL = b'2'


class SocketType(Enum):
    PULL_BIND = b'0'
    PULL_CONNECT = b'1'
    PUSH_BIND = b'2'
    PUSH_CONNECT = b'3'
    SUB_BIND = b'4'
    SUB_CONNECT = b'5'
    PUB_BIND = b'6'
    PUB_CONNECT = b'7'
    PAIR_BIND = b'8'
    PAIR_CONNECT = b'9'

    @property
    def is_bind(self):
        return self.value % 2 == 0


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


class Network:
    def __init__(self):
        self.ctx = zmq.Context()
        self.sockets = dict()
        self.pollers = dict()

    def build_socket(self, socket_type: 'SocketType', route: 'Route',
                     identity: str = None, name=None):
        """
        :param socket_type:
        :param name: string that gets hashed and determines port
        :param route: in/out/ctrl
        :param identity: pub/sub identity
        :return: zmq socket
        """
        sock = {
            SocketType.PULL_BIND: lambda: self.ctx.socket(zmq.PULL),
            SocketType.PULL_CONNECT: lambda: self.ctx.socket(zmq.PULL),
            SocketType.SUB_BIND: lambda: self.ctx.socket(zmq.SUB),
            SocketType.SUB_CONNECT: lambda: self.ctx.socket(zmq.SUB),
            SocketType.PUB_BIND: lambda: self.ctx.socket(zmq.PUB),
            SocketType.PUB_CONNECT: lambda: self.ctx.socket(zmq.PUB),
            SocketType.PUSH_BIND: lambda: self.ctx.socket(zmq.PUSH),
            SocketType.PUSH_CONNECT: lambda: self.ctx.socket(zmq.PUSH),
            SocketType.PAIR_BIND: lambda: self.ctx.socket(zmq.PAIR),
            SocketType.PAIR_CONNECT: lambda: self.ctx.socket(zmq.PAIR)
        }[socket_type]()

        if route == Route.IN:
            port = hash_string_between(name, MIN_PORT, MAX_PORT - round(DIFF / 2))
        elif route == Route.OUT:
            port = hash_string_between(name, MAX_PORT - round(DIFF / 2), MAX_PORT)
        elif route == Route.CTRL:
            port = ROUTER_PORT
        else:
            raise NotImplementedError

        if socket_type.is_bind:
            sock.bind('tcp://%s:%d' % (HOST, port))
        else:
            sock.connect('tcp://%s:%d' % (HOST, port))

        if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
            sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')

        # Note: the following very dangerous for pub-sub socketc
        sock.setsockopt(zmq.RCVHWM, 10)
        sock.setsockopt(zmq.RCVBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

        sock.setsockopt(zmq.SNDHWM, 10)
        sock.setsockopt(zmq.SNDBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

        self.sockets[route] = sock

    def build_poller(self, route: 'Route'):
        poller = zmq.Poller()
        poller.register(self.sockets[route], zmq.POLLIN)
        self.pollers[route] = poller

    def recv(self, route: 'Route'):
        """
        first byte designates the commands,
        eight characters are id and the rest is the message.
        """

        body = self.sockets[route].recv()
        cmd = Command(body[:1])
        msg_id = struct.unpack("L", body[:8])[0]
        msg = body[8:]

        return cmd, msg_id, msg

    def send(self, route: 'Route', cmd, msg_id: int, msg):
        msg_id = struct.pack("L", msg_id)
        self.sockets[route].send(cmd.value + msg_id + msg)

    def poll(self, route: 'Route'):
        """
        :param route: Route Object
        :return: True if messages exist for the route
        """
        return True if self.sockets[route] in dict(self.pollers[route].poll(0)) else False

    def close(self):
        for sock in self.sockets.values():
            sock.close()
        self.ctx.term()
