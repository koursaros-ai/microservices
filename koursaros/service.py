
from koursaros.streamer import get_hash_ports
from kctl.logger import set_logger
from grpc_tools import protoc
from threading import Thread
from pathlib import Path
from .yamls import Yaml
from sys import argv
import zmq


class Service:
    """The base service class"""

    def __init__(self):
        # set yamls
        self.service_yaml_path = Path(argv[1])
        self.service_yaml = Yaml(self.service_yaml_path)
        self.service_name = self.service_yaml_path.stem
        print()
        print(argv)

        raise SystemExit
        self.base_yaml = Yaml('base.yaml')

        # set messages
        self.compile_messages_proto('.')
        import messages_pb2
        self._rcv_proto = messages_pb2.__dict__.get(self.base_yaml.rcv_proto, None)
        self._send_proto = messages_pb2.__dict__.get(self.base_yaml.send_proto, None)

        # set zeromq
        self._context = zmq.Context()
        self._in_port, self._out_port = get_hash_ports(self.service_name, 2)
        self._rcv_host = "tcp://127.0.0.1:" + self._in_port
        self._send_host = "tcp://127.0.0.1:" + self._out_port
        self._stub_f = None

        # set logger
        set_logger(self.service_name)

        print(f'Initializing "{self.service_name}"')

    class Message:
        """Class to hold key word arguments for sending via protobuf"""
        __slots__ = ['kwargs']

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    @staticmethod
    def compile_messages_proto(path):
        print(f'Compiling messages for {path}')

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
        pull_socket.connect(self._rcv_host)
        print('Socket created on %s' % pull_socket)

        push_socket = self._context.socket(zmq.PUSH)
        push_socket.connect(self._send_host)
        print('Socket created on %s' % push_socket)

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
