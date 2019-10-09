

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


class ProtoType(Enum):
    RECV = b'0'
    SEND = b'1'


class Command(Enum):
    PASS = b'0'
    SEND = b'1'
    BIND = b'2'
    RESET = b'3'
    ACK = b'4'


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
        self.sockets = dict()
        self.ctx = zmq.Context()

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

    def recv(self, route: 'Route'):
        """
        first character is the router command, next
        sixteen are id, and last the rest is the message.
        """
        body = self.sockets[route].recv()
        cmd = Command(body[:1])
        msg_id = struct.unpack("xL", body[1:17])
        msg = body[17:]

        return cmd, msg_id, msg

    def send(self, route: 'Route', cmd: 'Command', msg_id: int, msg: 'bytes'):
        self.sockets[route].send(cmd.value + struct.pack("xL", msg_id) + msg)

    def close(self):
        for sock in self.sockets.values():
            sock.close()
        self.ctx.term()

    @staticmethod
    def get_proto_fields(proto_cls):
        return list(proto_cls.DESCRIPTOR.fields_by_name)