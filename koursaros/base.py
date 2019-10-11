
from kctl.logger import set_logger
from hashlib import sha1
from enum import Enum
import struct
import zmq
import pathlib
import sys

HOST = "127.0.0.1"
CTRL_PORT = 49152
MIN_PORT = 49153
MAX_PORT = 65536
DIFF = MAX_PORT - MIN_PORT
FLASK_PORT = 5000
POLL_TIMEOUT = 1000


class Command(Enum):
    SEND = b'0'
    CONFIG = b'1'
    ERROR = b'2'


class Route(Enum):
    IN = 0
    OUT = 1


class SocketType(Enum):
    REQ_BIND = 0
    REQ_CONNECT = 1
    REP_BIND = 2
    REP_CONNECT = 3
    PULL_BIND = 4
    PULL_CONNECT = 5
    PUSH_BIND = 6
    PUSH_CONNECT = 7
    SUB_BIND = 8
    SUB_CONNECT = 9
    PUB_BIND = 10
    PUB_CONNECT = 11
    PAIR_BIND = 12
    PAIR_CONNECT = 13

    @property
    def is_bind(self):
        return self.value % 2 == 0


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


class Messager:
    cmds = dict()
    ctx = zmq.Context()
    base_name = pathlib.Path(sys.argv[0]).parent.stem
    socket_in = None
    socket_out = None
    socket_ctrl = None

    def run(self):

        if self.base_name == 'ctrl':

        else:
            # poll ctrl for instructions
            self.socket_ctrl = self.build_socket(SocketType.REQ_CONNECT, CTRL_PORT)
            self.send(self.socket_ctrl, Command.CONFIG)

    def build_socket(self, socket_type: 'SocketType', port: int, identity: str = None):
        """
        :param socket_type:
        :param name: string that gets hashed and determines port
        :param route: in/out
        :param identity: pub/sub identity
        :return: zmq socket
        """
        sock = {
            SocketType.PULL_BIND: lambda: self.ctx.socket(zmq.PULL),
            SocketType.PULL_BIND: lambda: self.ctx.socket(zmq.PULL),
            SocketType.PULL_CONNECT: lambda: self.ctx.socket(zmq.PULL),
            SocketType.SUB_BIND: lambda: self.ctx.socket(zmq.SUB),
            SocketType.SUB_CONNECT: lambda: self.ctx.socket(zmq.SUB),
            SocketType.PUB_BIND: lambda: self.ctx.socket(zmq.PUB),
            SocketType.PUB_CONNECT: lambda: self.ctx.socket(zmq.PUB),
            SocketType.PUSH_BIND: lambda: self.ctx.socket(zmq.PUSH),
            SocketType.PUSH_CONNECT: lambda: self.ctx.socket(zmq.PUSH),
            SocketType.PAIR_BIND: lambda: self.ctx.socket(zmq.PAIR),
            SocketType.PAIR_CONNECT: lambda: self.ctx.socket(zmq.PAIR),
        }[socket_type]()

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

        return sock

    @staticmethod
    def build_poller(self, socket: 'SocketType'):
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        return poller

    def recv(self, socket: 'zmq.Socket'):
        """
        first byte designates the commands,
        eight characters are id and the rest is the message.
        """

        body = socket.recv()
        cmd = Command(body[:1])

        if cmd == Command.SEND:
            msg_id = struct.unpack("L", body[1:9])[0]
            msg = msg_id, body[9:]
        elif cmd == Command.CONFIG:

            msg = None

        self.cmds[cmd](msg)

    def send(self, socket: 'zmq.Socket', cmd: 'Command', *msg):
        # msg_id = struct.pack("L", msg_id)
        socket.send(cmd.value + b''.join(msg))

    def close(self):
        self.socket_in.close()
        self.socket_out.close()
        self.socket_ctrl.close()
        self.ctx.term()
