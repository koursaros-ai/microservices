
from koursaros.streamer import get_hash_ports
from kctl.logger import set_logger
from grpc_tools import protoc
from threading import Thread
from pathlib import Path
from .yamls import Yaml
import json
import sys
import zmq
import os

HOST = "tcp://127.0.0.1:{}"


class Service:
    """The base service class"""

    def __init__(self):
        # set yamls
        self._service_yaml_path = Path(sys.argv[1])
        self.service_yaml = Yaml(self._service_yaml_path)
        self._service_name = self._service_yaml_path.stem
        _base_dir_path = Path(sys.argv[0]).parent
        self.base_yaml = Yaml(_base_dir_path.joinpath('base.yaml'))

        # set logger
        self.logger = set_logger(self._service_name)

        # set directories
        os.chdir(_base_dir_path)
        sys.path.insert(1, str(_base_dir_path))

        # compile messages
        self.compile_messages_proto(_base_dir_path)
        messages = __import__('messages_pb2')
        self._rcv_proto_cls = messages.__dict__.get(self.base_yaml.rcv_proto)
        self._send_proto_cls = messages.__dict__.get(self.base_yaml.send_proto)

        # set zeromq
        self._context = zmq.Context()
        self._in_port, self._out_port = get_hash_ports(self._service_name, 2)
        self._rcv_address = HOST.format(self._in_port)
        self._send_address = HOST.format(self._out_port)
        self._stub_f = None

        self.logger.info(f'Initializing "{self._service_name}"')

        self._pull_socket = self._context.socket(zmq.PULL)
        self._pull_socket.connect(self._rcv_address)
        self.logger.bold('PULL socket connected on %s' % self._rcv_address)

        self._push_socket = self._context.socket(zmq.PUSH)
        self._push_socket.connect(self._send_address)
        self.logger.bold('PUSH socket connected on %s' % self._send_address)

    class Message:
        """Class to hold key word arguments for sending via protobuf"""
        __slots__ = ['kwargs']

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __repr__(self):
            return 'Message:\n' + json.dumps(self.kwargs, indent=4)

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

    def _protofy(self, msg, proto_cls):
        if isinstance(msg, self.Message):
            return proto_cls(**msg.kwargs)
        elif isinstance(msg, proto_cls):
            return msg
        else:
            raise TypeError('Cannot cast type "%s" to protobuf' % type(msg))

    @staticmethod
    def _proto_to_bytes(proto):
        return proto.SerializeToString()

    @staticmethod
    def _bytes_to_proto(byte, proto_cls):
        import pdb; pdb.set_trace()
        return proto_cls.ParseFromString(byte)

    def _check_rcv_proto(self, proto):
        pass

    def _check_send_proto(self, proto):
        pass

    def _check_return_msg(self, msg):
        if msg is None:
            raise ValueError('Send stub must return...')

    def _stub(self, msg):
        """
        The stub receives a message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned

        :param msg: Service.Message or Proto Class
        :return body:
        """
        self.logger.info('Stub received %s' % msg)

        proto = self._protofy(msg, self._rcv_proto_cls)
        self._check_rcv_proto(proto)

        msg = self._stub_f(proto)
        self.logger.info('Returned from stub: %s' % msg)
        self._check_return_msg(msg)

        proto = self._protofy(msg, self._send_proto_cls)
        self._check_send_proto(proto)
        self.logger.info('Sending proto')
        self._push(proto)

    def _pull(self):
        """
        :return: protobuf instance
        """
        body = self._pull_socket.recv()
        proto = self._bytes_to_proto(body, self._rcv_proto_cls)
        return proto

    def _push(self, proto):
        """
        :param proto: protobuf instance
        """
        self.logger.info('Sending body')
        body = self._proto_to_bytes(proto)
        self._push_socket.send(body)

    def _serve(self):
        """
        Executes a push pull loop, executing the stub as a callback
        """
        while True:
            msg = self._pull()
            self.logger.info('Received %s' % msg)
            self._stub(msg)

    def run(self, subs=None):
        """Takes optional sub functions to run in separate threads

        :param subs: optional iterable of callback funcs
        """
        threads = []

        if subs is not None:
            for sub in subs:
                self.logger.info('Running thread "%s"' % sub.__name__)
                t = Thread(target=sub)
                t.start()
                threads += [t]

        t = Thread(target=self._serve)
        t.start()
        threads += [t]

        for t in threads:
            t.join()
