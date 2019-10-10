
from kctl.logger import set_logger
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
    ERROR = b'2'


class Route(Enum):
    IN = 0
    OUT = 1
    CTRL = 2


class SocketType(Enum):
    PULL_BIND = 0
    PULL_CONNECT = 1
    PUSH_BIND = 2
    PUSH_CONNECT = 3
    SUB_BIND = 4
    SUB_CONNECT = 5
    PUB_BIND = 6
    PUB_CONNECT = 7
    PAIR_BIND = 8
    PAIR_CONNECT = 9

    @property
    def is_bind(self):
        return self.value % 2 == 0


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


class Network:
    def __init__(self, context):
        self.ctx = zmq.Context()
        self.sockets = dict()
        self.pollers = dict()
        self.logger = set_logger(context)

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

        if route == Route.CTRL:
            port = ROUTER_PORT
        else:
            hashed = hash_string_between(name, 0, round((MAX_PORT - MIN_PORT) / 2))
            xor = route.value ^ socket_type.value % 2
            port = hashed + hashed * xor + MIN_PORT

        tcp = 'tcp://%s:%d' % (HOST, port)

        if socket_type.is_bind:
            sock.bind(tcp)
        else:
            sock.connect(tcp)

        if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
            sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')

        # Note: the following very dangerous for pub-sub socketc
        sock.setsockopt(zmq.RCVHWM, 10)
        sock.setsockopt(zmq.RCVBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

        sock.setsockopt(zmq.SNDHWM, 10)
        sock.setsockopt(zmq.SNDBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

        self.logger.bold('%s built on %s using hash: %s' % (socket_type, tcp, name))
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
        msg_id = struct.unpack("L", body[1:9])[0]
        msg = body[9:]

        return cmd, msg_id, msg

    def send(self, route: 'Route', cmd, msg_id: int, msg):
        msg_id = struct.pack("L", msg_id)

        self.logger.bold(cmd)
        self.logger.bold(msg_id)
        self.logger.bold(msg)

        self.sockets[route].send(cmd.value + msg_id + msg)

    def poll(self, route: 'Route'):
        """
        :param route: Route Object
        :return: True if messages exist for the route
        """
        return True if self.sockets[route] in dict(self.pollers[route].poll(0)) else False

    def setsockopt(self, route: 'Route', *args):
        self.sockets[route].setsockopt(*args)

    def close(self):
        for sock in self.sockets.values():
            sock.close()
        self.ctx.term()
