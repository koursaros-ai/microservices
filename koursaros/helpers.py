import struct
from hashlib import sha1
from typing import List

__all__ = ['_parse_msg', '_int_to_16byte', '_16byte_to_int',
           'ROUTER_ADDRESS', 'hash_string_between', 'get_hash_ports',
           'HOST', 'FLASK_PORT']

HOST = "tcp://127.0.0.1:%s"
ROUTER_ADDRESS = HOST % 49152
MIN_PORT = 49153
MAX_PORT = 65536
FLASK_PORT = 5000


def _parse_msg(body):
    """
    first character is the router command, next
    sixteen are id, and last the rest is the message.

    :param body: bytes message
    :return command, msg_id, msg
    """
    return body[:1], body[1:17], body[18:]


def _int_to_16byte(integer):
    return struct.pack("xL", integer)


def _16byte_to_int(byte):
    return struct.unpack("xL", byte)


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


def get_hash_ports(string: str, num_ports: int) -> List[int]:
    diff = MAX_PORT - MIN_PORT
    h = hash_string_between(string, 0, round(diff / num_ports))
    return [h * (i + 1) + MIN_PORT for i in range(num_ports)]