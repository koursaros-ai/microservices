from .network import Network, Route, SocketType, Command
from .messages import MsgType, Messages
from kctl.logger import set_logger
from .yamls import Yaml
import pathlib
import zmq
import sys
import os

RCV_TIMEOUT = 10000


class Service:
    """The base service class"""

    def __init__(self):
        # set yamls
        base_dir_path = pathlib.Path(sys.argv[0]).parent
        self.base_yaml = Yaml(base_dir_path.joinpath('base.yaml'))
        yaml_path = pathlib.Path(sys.argv[1])
        self.yaml = Yaml(yaml_path)
        pipe_yaml = Yaml(pathlib.Path(sys.argv[2]))

        # set metadata
        name = yaml_path.stem
        position = pipe_yaml.services.index(name)
        self.position = -1 if pipe_yaml.services[-1] == name else position

        # set logger
        self.logger = set_logger(name)
        self.logger.info('Initializing "{}"')

        # set directories
        os.chdir(base_dir_path)
        sys.path.insert(1, str(base_dir_path))

        # defaults
        self._stub = None
        self.sent = 0
        self.base_dir_path = base_dir_path
        self.name = name

    def stub(self, f):
        self._stub = f

    @property
    def status(self):
        return dict(
            pid=os.getpid(),
            service=self.name,
            sent=self.sent,
            position=self.position
        )

    def run(self):

        # compile messages
        msgs = Messages(proto_module=self.base_dir_path,
                        send_proto=self.base_yaml.recv_proto,
                        recv_proto=self.base_yaml.send_proto)

        # set network
        net = Network()
        net.build_socket(SocketType.PULL_CONNECT, Route.IN, name=self.name)
        net.build_socket(SocketType.PUSH_CONNECT, Route.OUT, name=self.name)
        net.build_socket(SocketType.SUB_CONNECT, Route.CTRL, name=self.name)
        net.build_poller(Route.CTRL)
        net.setsockopt(Route.IN, zmq.RCVTIMEO, RCV_TIMEOUT)

        while True:
            # if message from router, send status
            if net.poll(Route.CTRL):
                status = msgs.cast(self.status, MsgType.JSON, MsgType.JSONBYTES)
                net.send(Route.OUT, Command.STATUS, 0, status)

            cmd, msg_id, msg = net.recv(Route.IN)

            # if receiving status from preceding service, resend
            if cmd == Command.STATUS:
                net.send(Route.OUT, cmd, msg_id, msg)

            elif cmd == Command.SEND:

                # if first position then get jsons from router
                if self.position == 0:
                    proto = msgs.cast(msg, MsgType.JSONBYTES, MsgType.RECV_PROTO)
                else:
                    proto = msgs.cast(msg, MsgType.PROTOBYTES, MsgType.RECV_PROTO)
                returned = self._stub(proto)

                if isinstance(returned, dict):
                    msg = msgs.cast(returned, MsgType.KWARGS, MsgType.SEND_PROTO)

                # if last position then send jsons to router
                if self.position == -1:
                    msg = msgs.cast(msg, MsgType.SEND_PROTO, MsgType.JSONBYTES)
                else:
                    msg = msgs.cast(msg, MsgType.SEND_PROTO, MsgType.PROTOBYTES)

                net.send(Route.OUT, Command.SEND, msg_id, msg)
