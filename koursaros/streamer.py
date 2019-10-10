
from .network import Network, Route, SocketType
from kctl.logger import set_logger
import sys
import zmq


class Streamer:
    """The base streamer class"""

    def __init__(self):
        self.service_in = sys.argv[1]
        self.service_out = sys.argv[2]

        # set logger
        name = "{}->{}".format(self.service_in[:5], self.service_out[:5])
        self.logger = set_logger(name)
        self.logger.info('Initializing {} streamer'.format(name))
        self.name = name

    def run(self):
        net = Network(self.name)
        net.build_socket(SocketType.PUSH_BIND, Route.IN, name=self.service_in)
        net.build_socket(SocketType.PULL_BIND, Route.OUT, name=self.service_out)
        zmq.device(zmq.STREAMER, net.sockets[Route.IN], net.sockets[Route.OUT])
        net.close()


if __name__ == "__main__":
    s = Streamer()
    s.run()
