
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
MSG_BASE = b'koursaros:'


class Service:
    """The base service class"""

    def __init__(self):
        # set yamls
        service_yaml_path = Path(sys.argv[1])
        self.service_yaml = Yaml(service_yaml_path)
        service_name = service_yaml_path.stem
        _base_dir_path = Path(sys.argv[0]).parent
        self.base_yaml = Yaml(_base_dir_path.joinpath('base.yaml'))

        # set logger
        self.logger = set_logger(service_name)
        self.logger.info(f'Initializing "%s"' % service_name)

        # set directories
        os.chdir(_base_dir_path)
        sys.path.insert(1, str(_base_dir_path))

        # compile messages
        self._compile_messages_proto(_base_dir_path)
        messages = __import__('messages_pb2')
        self._rcv_proto_cls = messages.__dict__.get(self.base_yaml.rcv_proto)
        self._send_proto_cls = messages.__dict__.get(self.base_yaml.send_proto)
        self._msg_tag = MSG_BASE + (service_name + ':').encode()

        # set zeromq
        context = zmq.Context()
        in_port, out_port = get_hash_ports(service_name, 2)
        rcv_address = HOST.format(in_port)
        send_address = HOST.format(out_port)
        self._pull_socket = context.socket(zmq.PULL)
        self._pull_socket.connect(rcv_address)
        self.logger.bold('PULL socket connected on %s' % rcv_address)
        self._push_socket = context.socket(zmq.PUSH)
        self._push_socket.connect(send_address)
        self.logger.bold('PUSH socket connected on %s' % send_address)
        self._stub_f = None
        self._cb_f = None

    class Message:
        """Class to hold key word arguments for sending via protobuf"""
        __slots__ = ['kwargs']

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __repr__(self):
            return 'Message:\n' + json.dumps(self.kwargs, indent=4)

    def _compile_messages_proto(self, path):
        self.logger.info(f'Compiling messages for "{path}"...')

        protoc.main((
            '',
            f'-I={path}',
            f'--python_out={path}',
            f'{path}/messages.proto',
        ))

    def stub(self, f):
        self._stub_f = f
        return self._rcv

    def callback(self, f):
        self._cb_f = f
        return f

    def _protofy(self, msg, proto_cls):
        if isinstance(msg, proto_cls):
            return msg
        elif isinstance(msg, self.Message):
            return proto_cls(**msg.kwargs)
        elif isinstance(msg, bytes):
            proto = proto_cls()
            proto.ParseFromString(msg)
            return proto
        else:
            raise TypeError('Cannot cast type "%s" to protobuf' % type(msg))

    @staticmethod
    def _proto_to_bytes(proto):
        return proto.SerializeToString()

    def _check_rcv_proto(self, proto):
        pass

    def _check_send_proto(self, proto):
        pass

    def _check_return_msg(self, msg):
        if msg is None:
            raise ValueError('Send stub must return...')

    def _rcv(self, msg, msg_tag=b''):
        """
        The stub receives a message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned

        :param msg: Service.Message, Proto Class, or binary message
        """
        proto = self._protofy(msg, self._rcv_proto_cls)
        self._check_rcv_proto(proto)
        self.logger.info(msg_tag)
        if msg_tag == self._msg_tag:
            self._cb_f(proto)
        else:
            msg = self._stub_f(proto)
            self._check_return_msg(msg)

            proto = self._protofy(msg, self._send_proto_cls)
            self._check_send_proto(proto)
            self._send(proto, msg_tag)

    def _send(self, proto, msg_tag):
        """
        Append the current service's msg tag if
        the message didn't come with one...

        :param proto: protobuf instance
        """
        if msg_tag == b'':
            msg_tag = self._msg_tag

        body = self._proto_to_bytes(proto)
        self._push_socket.send(msg_tag + body)

    @staticmethod
    def find_nth(string, substr, n):
        """find nth occurrence of substring"""
        start = string.find(substr)
        while start >= 0 and n > 1:
            start = string.find(substr, start + len(substr))
            n -= 1
        return start

    def _pop_msg_tag(self, body):
        """
        Pops off the message tag and returns it with the
        rest of the body.

        :param body: binary protobuf message
        :return: msg_tag, body
        """
        if body.startswith(MSG_BASE):
            second_colon = self.find_nth(body, b':', 2)
            msg_tag = body[:second_colon + 1]
            return msg_tag, body[second_colon + 1:]
        else:
            return b'', body

    def _serve(self):
        """
        Executes a push pull loop, executing _rcv as a callback
        """
        while True:
            body = self._pull_socket.recv()
            msg_tag, body = self._pop_msg_tag(body)
            self._rcv(body, msg_tag=msg_tag)

    def run(self, subs=None):
        """
        Takes optional sub functions to run in separate threads

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
