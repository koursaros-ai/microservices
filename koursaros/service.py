
from koursaros.streamer import get_hash_ports, HOST
from kctl.logger import set_logger
from grpc_tools import protoc
from threading import Thread
from pathlib import Path
from .yamls import Yaml
from sys import argv
import sys
import zmq
import os


class Service:
    """The base service class"""

    def __init__(self):
        # set yamls
        self._service_yaml_path = Path(argv[1])
        self.service_yaml = Yaml(self._service_yaml_path)
        self._service_name = self._service_yaml_path.stem
        _base_dir_path = Path(argv[0]).parent
        self.base_yaml = Yaml(_base_dir_path.joinpath('base.yaml'))

        # set directories
        os.chdir(_base_dir_path)
        sys.path.insert(1, str(_base_dir_path))

        # compile messages
        self.compile_messages_proto(_base_dir_path)
        messages = __import__('messages_pb2')
        self._rcv_proto = messages.__dict__.get(self.base_yaml.rcv_proto)
        self._send_proto = messages.__dict__.get(self.base_yaml.send_proto)

        # set zeromq
        self._context = zmq.Context()
        self._in_port, self._out_port = get_hash_ports(self._service_name, 2)
        self._rcv = HOST.format(self._in_port)
        self._send = HOST.format(self._out_port)
        self._stub_f = None

        # set logger
        self.logger = set_logger(self._service_name)

        self.logger.info(f'Initializing "{self._service_name}"')

    class Message:
        """Class to hold key word arguments for sending via protobuf"""
        __slots__ = ['kwargs']

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def compile_messages_proto(self, path):
        self.logger.info(f'Compiling messages for "{path}"...')

        protoc.main((
            '',
            f'-I={path}',
            f'--python_out={path}',
            f'{path}/messages.proto',
        ))

    def stub(self, f):
        self._stub_f = f
        return self._stub

    def _protofy(self, msg, proto):
        """Checks whether the type is Message else it assumes it's a proto"""
        return proto(**msg.kwargs) if type(msg) == self.Message else msg

    def _check_rcv_proto(self, proto):
        pass

    def _check_send_proto(self, proto):
        pass

    def _check_return_msg(self, msg):
        if msg is not None:
            raise ValueError('Send stub must return...')

    def _stub(self, msg):
        """
        The stub receives a binary message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned

        :param msg:
        :return:
        """
        proto = self._protofy(msg, self._rcv_proto)
        self._check_rcv_proto(proto)
        msg = self._stub_f(proto)
        self._check_return_msg(msg)
        proto = self._send_proto(**msg.kwargs)
        self._check_send_proto(proto)
        body = proto.SerializeToString()
        return body

    def _push_pull(self):
        """
        Executes a push pull loop, executing the stub as a callback 
        """

        pull_socket = self._context.socket(zmq.PULL)
        pull_socket.connect(self._rcv)
        self.logger.info('PULL socket created on %s' % self._rcv)

        push_socket = self._context.socket(zmq.PUSH)
        push_socket.connect(self._send)
        self.logger.info('PUSH socket created on %s' % self._send)

        while True:
            msg = pull_socket.recv()
            body = self._stub(msg)
            push_socket.send(body)

    def run(self, subs=None):
        """Takes optional sub functions to run in separate threads

        :param subs: optional iterable of callback funcs
        """
        threads = []

        if subs is not None:
            for sub in subs:
                t = Thread(target=sub)
                t.start()
                threads += [t]

        t = Thread(target=self._push_pull)
        t.start()
        threads += [t]

        for t in threads:
            t.join()
