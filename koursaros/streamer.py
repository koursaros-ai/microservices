
from kctl.logger import set_logger
from hashlib import sha1
from typing import List
from sys import argv
import zmq

HOST = "tcp://*:{}"

MIN_PORT = 49153
MAX_PORT = 65536


def hash_string_between(string: str, min_num: int, max_num: int):
    return int(sha1(string.encode()).hexdigest(), 16) % (max_num - min_num) + min_num


def get_hash_ports(string: str, num_ports: int) -> List[int]:
    diff = MAX_PORT - MIN_PORT
    h = hash_string_between(string, 0, round(diff / num_ports))
    return [h * (i + 1) + MIN_PORT for i in range(num_ports)]


class Streamer:
    """The base streamer class"""

    def __init__(self):
        # set yamls
        self.service_in = argv[1]
        self.service_out = argv[2]

        # set logger
        self.name = "{}->{}".format(self.service_in[:5], self.service_out[:5])
        self.logger = set_logger(self.name)

        # set zeromq
        self.context = zmq.Context()
        _, self.in_port = get_hash_ports(self.service_in, 2)
        self.out_port, _ = get_hash_ports(self.service_out, 2)

        self._rcv = HOST.format(in_port)
        self._send = HOST.format(out_port)

        self.logger.info('Initializing {} streamer'.format(self.name))

        self.pull_socket = self.context.socket(zmq.PULL)
        self.pull_socket.bind(self._rcv)
        self.logger.bold(
            'Socket bound on {} to PULL from {}'.format(self._rcv, self.service_in))

        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.bind(self._send)
        self.logger.bold(
            'Socket bound on {} to PUSH to {}'.format(self._send, self.service_out))



    def stream(self):
        zmq.device(zmq.STREAMER, self.pull_socket, self.push_socket)
        self.pull_socket.close()
        self.push_socket.close()
        self.context.term()


if __name__ == "__main__":
    s = Streamer()
    s.expose()
    s.stream()
