
from kctl.logger import set_logger
from pathlib import Path
from hashlib import sha1
from typing import List
from sys import argv
import zmq

MIN_PORT = 49152
MAX_PORT = 65536


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string).hexdigest(), 16) % (max_num - min_num) + min_num


def get_hash_ports(string: str, num_ports: int) -> List[int]:
    diff = MAX_PORT - MIN_PORT
    h = hash_string_between(string, 0, round(diff / num_ports))
    return [h * i for i in range(num_ports)]


class Streamer:
    """The base streamer class"""

    def __init__(self):
        # set yamls
        self._service_in = Path(argv[1])
        self._service_out = Path(argv[2])

        # set zeromq
        self._context = zmq.Context()
        _, self._in_port = get_hash_ports(self._service_in, 2)
        self._out_port, _ = get_hash_ports(self._service_out, 2)
        self._rcv_host = "tcp://127.0.0.1:" + self._in_port
        self._send_host = "tcp://127.0.0.1:" + self._out_port

        # set logger
        self.name = "{}->{}".format(self._service_in[:5], self._service_out[:5])

        print('Initializing {} streamer'.format(self.name))

    def push_pull(self):
        """
        Executes a push pull loop, executing the stub as a callback
        """

        push_socket = self._context.socket(zmq.PUSH)
        push_socket.connect(push_socket)
        print('Socket created on ' + push_socket)

        pull_socket = self._context.socket(zmq.PULL)
        pull_socket.connect(pull_socket)
        print('Socket created on ' + pull_socket)

        while True:
            msg = pull_socket.recv()
            push_socket.send(msg)


if __name__ == "__main__":
    s = Streamer()
    s.push_pull()
