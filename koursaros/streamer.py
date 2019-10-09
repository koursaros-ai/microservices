from kctl.logger import set_logger
from .helpers import *
from sys import argv
import zmq


class Streamer:
    """The base streamer class"""

    def __init__(self):
        # set yamls
        service_in = argv[1]
        service_out = argv[2]

        # set logger
        name = "{}->{}".format(service_in[:5], service_out[:5])
        logger = set_logger(name)

        # set zeromq
        self.context = zmq.Context()
        _, in_port = get_hash_ports(service_in, 2)
        out_port, _ = get_hash_ports(service_out, 2)

        rcv_address = HOST.format(in_port)
        send_address = HOST.format(out_port)

        logger.info('Initializing {} streamer'.format(name))

        self.pull_socket = self.context.socket(zmq.PULL)
        import pdb; pdb.set_trace()
        self.pull_socket.bind(rcv_address)
        logger.bold('Socket bound on {} to PULL from {}'
                    .format(rcv_address, service_in))

        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.bind(send_address)
        logger.bold('Socket bound on {} to PUSH to {}'
                    .format(send_address, service_out))

    def stream(self):
        zmq.device(zmq.STREAMER, self.pull_socket, self.push_socket)
        self.pull_socket.close()
        self.push_socket.close()
        self.context.term()


if __name__ == "__main__":
    s = Streamer()
    s.stream()
