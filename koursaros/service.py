from .network import Network, Route, SocketType, Command
from .messages import MsgType, Messages, ParseError
from kctl.logger import set_logger
from traceback import format_exc
from .yamls import Yaml
import pathlib
import time
import zmq
import sys
import os

RCV_TIMEOUT = 1000
HEARTBEAT = 5


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
        self.logger.info('Initializing "%s"' % name)

        # set directories
        os.chdir(base_dir_path)
        sys.path.insert(1, str(base_dir_path))

        # defaults
        self._stub = None
        self.base_dir_path = base_dir_path
        self.name = name
        self.errors = 0
        self.last_error = None
        self.sent = 0
        self.last_status = 0
        self.last_error_time = None

    def stub(self, f):
        self._stub = f

    @property
    def status(self):
        return {
            self.name: {
                os.getpid(): {
                    'sent': self.sent,
                    'errors': self.errors,
                    'last_error': self.last_error,
                    'last_error_time': self.last_error_time,
                    'last_heartbeat': time.time()
                }
            }
        }

    def register_sync_error(self, e, msg_id):
        self.register_async_error(e)
        self.net.send(Route.OUT, Command.ERROR, msg_id, self.status)

    def register_async_error(self, e):
        self.errors += 1
        self.last_error = repr(e)
        self.last_error_time = time.time()

    def run(self):

        # compile messages
        msgs = Messages(proto_module=self.base_dir_path,
                        send_proto=self.base_yaml.recv_proto,
                        recv_proto=self.base_yaml.send_proto)

        # set network
        self.net = Network(self.name)
        self.net.build_socket(SocketType.PULL_CONNECT, Route.IN, name=self.name)
        self.net.build_socket(SocketType.PUSH_CONNECT, Route.OUT, name=self.name)
        self.net.build_poller(Route.IN)
        self.net.setsockopt(Route.IN, zmq.RCVTIMEO, RCV_TIMEOUT)

        while True:
            if self.last_status - time.time() > HEARTBEAT:
                status = msgs.cast(self.status, MsgType.JSON, MsgType.JSONBYTES)
                self.net.send(Route.OUT, Command.STATUS, 0, status)

            try:
                cmd, msg_id, msg = self.net.recv(Route.IN)
            except zmq.error.Again:
                # timeout
                continue

            self.logger.info('received msg %s with cmd %s...' % (msg, cmd))

            # if receiving status msg then resend
            if cmd in (Command.STATUS, Command.ERROR):
                self.net.send(Route.OUT, cmd, msg_id, msg)
                continue

            elif cmd == Command.SEND:

                # if first position then get jsons from router
                if self.position == 0:
                    try:
                        proto = msgs.cast(msg, MsgType.JSONBYTES, MsgType.RECV_PROTO)
                    except ParseError as e:
                        self.register_sync_error(e, msg_id)
                        continue

                else:
                    proto = msgs.cast(msg, MsgType.PROTOBYTES, MsgType.RECV_PROTO)

                try:
                    returned = self._stub(proto)
                except:
                    self.register_sync_error(format_exc(), msg_id)
                    continue

                if isinstance(returned, dict):
                    proto = msgs.cast(returned, MsgType.KWARGS, MsgType.SEND_PROTO)
                else:
                    proto = returned

                # if last position then send jsons to router
                if self.position == -1:
                    msg = msgs.cast(proto, MsgType.SEND_PROTO, MsgType.JSONBYTES)
                else:
                    msg = msgs.cast(proto, MsgType.SEND_PROTO, MsgType.PROTOBYTES)

                self.net.send(Route.OUT, Command.SEND, msg_id, msg)
                self.sent += 1
