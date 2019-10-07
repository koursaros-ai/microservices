
from zmq.devices.basedevice import ProcessDevice
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

        # set logger
        self._name = "{}->{}".format(self._service_in[:5], self._service_out[:5])
        set_logger(self._name)

        # set zeromq
        _, self._in_port = get_hash_ports(self._service_in, 2)
        self._out_port, _ = get_hash_ports(self._service_out, 2)
        self._rcv_host = "tcp://127.0.0.1:" + self._in_port
        self._send_host = "tcp://127.0.0.1:" + self._out_port

        print('Initializing {} streamer'.format(self._name))

    def stream(self):
        """
        Executes a push pull loop, executing the stub as a callback
        """

        device = ProcessDevice(zmq.STREAMER, zmq.PULL, zmq.PUSH)
        print('{} PULL on {} and PUSH on {}'.format(
            self._name, self._rcv_host, self._send_host))

        device.bind_in(self._rcv_host)
        device.bind_out(self._send_host)

        device.setsockopt_in(zmq.IDENTITY, 'PULL')
        device.setsockopt_out(zmq.IDENTITY, 'PUSH')

        device.start()


if __name__ == "__main__":
    s = Streamer()
    s.stream()
