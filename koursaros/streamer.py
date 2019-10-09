from kctl.logger import set_logger
from .helpers import *
import sys
import zmq


class Streamer:
    """The base streamer class"""

    def __init__(self):
        cmd = sys.argv
        verbose = True if '--verbose' in cmd else False
        cmd.remove('--verbose')

        # set yamls
        self.service_in = cmd[1]
        self.service_out = cmd[2]

        # set logger
        name = "{}->{}".format(self.service_in[:5], self.service_out[:5])
        self.logger = set_logger(name, verbose=verbose)

        # set zeromq
        self.context = zmq.Context()
        _, self.in_port = get_hash_ports(self.service_in, 2)
        self.out_port, _ = get_hash_ports(self.service_out, 2)

        self.logger.info('Initializing {} streamer, verbose: {}'.format(name, verbose))

        self.push_socket = self.context.socket(zmq.PUSH)
        self.pull_socket = self.context.socket(zmq.PULL)

    def stream(self):
        rcv_address = HOST % self.in_port
        send_address = HOST % self.out_port

        # pull
        self.pull_socket.bind(rcv_address)
        self.logger.bold('Socket bound on {} to PULL from {}'
                         .format(rcv_address, self.service_in))

        self.push_socket.bind(send_address)
        self.logger.bold('Socket bound on {} to PUSH to {}'
                         .format(send_address, self.service_out))

        zmq.device(zmq.STREAMER, self.pull_socket, self.push_socket)
        self.pull_socket.close()
        self.push_socket.close()
        self.context.term()


if __name__ == "__main__":
    s = Streamer()
    s.stream()
