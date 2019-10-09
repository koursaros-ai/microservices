from .router import RouterCmd
from hashlib import sha1
from typing import List
import struct
from enum import Enum


__all__ = ['_pack_msg', '_unpack_msg', 'ROUTER_ADDRESS',
           'hash_string_between', 'get_hash_ports',
           'HOST', 'FLASK_PORT', 'get_proto_fields', 'POLL_TIMEOUT']

HOST = "tcp://127.0.0.1:%s"
ROUTER_ADDRESS = HOST % 49152
MIN_PORT = 49153
MAX_PORT = 65536
FLASK_PORT = 5000
POLL_TIMEOUT = 1000


def _unpack_msg(body):
    """
    first character is the router command, next
    sixteen are id, and last the rest is the message.

    :param body: bytes message
    :return command: RouterCmd
    :return msg_id: int
    :return: bytes message
    """
    return RouterCmd(body[:1]), struct.unpack("xL", body[1:17]), body[17:]


def _pack_msg(command, msg_id, msg):
    """
    Reverse of unpack

    :param command: RouterCmd
    :param msg_id: int
    :param msg: bytes message
    :return: bytes message
    """
    return command.value + struct.pack("xL", msg_id) + msg


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


def get_hash_ports(string: str, num_ports: int) -> List[int]:
    diff = MAX_PORT - MIN_PORT
    h = hash_string_between(string, 0, round(diff / num_ports))
    return [h * (i + 1) + MIN_PORT for i in range(num_ports)]


def get_proto_fields(proto_cls):
    return list(proto_cls.DESCRIPTOR.fields_by_name)


# class SocketType(Enum):
#     PULL_BIND = 0
#     PULL_CONNECT = 1
#     PUSH_BIND = 2
#     PUSH_CONNECT = 3
#     SUB_BIND = 4
#     SUB_CONNECT = 5
#     PUB_BIND = 6
#     PUB_CONNECT = 7
#     PAIR_BIND = 8
#     PAIR_CONNECT = 9
#
#     @property
#     def is_bind(self):
#         return self.value % 2 == 0



# def build_socket(
#         ctx: 'zmq.Context',
#         host: str, port: int,
#         socket_type: 'SocketType',
#         identity: 'str' = None) -> Tuple[ 'zmq.Socket', str]:
#
#     sock = {
#         SocketType.PULL_BIND: lambda: ctx.socket(zmq.PULL),
#         SocketType.PULL_CONNECT: lambda: ctx.socket(zmq.PULL),
#         SocketType.SUB_BIND: lambda: ctx.socket(zmq.SUB),
#         SocketType.SUB_CONNECT: lambda: ctx.socket(zmq.SUB),
#         SocketType.PUB_BIND: lambda: ctx.socket(zmq.PUB),
#         SocketType.PUB_CONNECT: lambda: ctx.socket(zmq.PUB),
#         SocketType.PUSH_BIND: lambda: ctx.socket(zmq.PUSH),
#         SocketType.PUSH_CONNECT: lambda: ctx.socket(zmq.PUSH),
#         SocketType.PAIR_BIND: lambda: ctx.socket(zmq.PAIR),
#         SocketType.PAIR_CONNECT: lambda: ctx.socket(zmq.PAIR)
#     }[socket_type]()
#
#     if socket_type.is_bind:
#         host = BaseService.default_host
#         if port is None:
#             sock.bind_to_random_port('tcp://%s' % host)
#         else:
#             sock.bind('tcp://%s:%d' % (host, port))
#     else:
#         if port is None:
#             sock.connect(host)
#         else:
#             sock.connect('tcp://%s:%d' % (host, port))
#
#     if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
#         sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')
#         # sock.setsockopt(zmq.SUBSCRIBE, b'')
#
#     # Note: the following very dangerous for pub-sub socketc
#     sock.setsockopt(zmq.RCVHWM, 10)
#     sock.setsockopt(zmq.RCVBUF, 10 * 1024 * 1024)  # limit of network buffer 100M
#
#     sock.setsockopt(zmq.SNDHWM, 10)
#     sock.setsockopt(zmq.SNDBUF, 10 * 1024 * 1024)  # limit of network buffer 100M
#
#     return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)