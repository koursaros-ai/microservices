from kctl.logger import KctlLogger
from threading import Thread
from sys import argv
import pdb; pdb.set_trace()
import messages_pb2
import zmq


class Service:
    """The base service class

    :param package: __package__ parameter
    """

    def __init__(self, package):
        self._context = zmq.Context()
        self._rcv_proto = messages_pb2.__dict__.get(argv[1], None)
        self._send_proto = messages_pb2.__dict__.get(argv[2], None)
        self._cb_proto = messages_pb2.__dict__.get(argv[3], None)

        self._rcv_host = "tcp://127.0.0.1" + argv[3]
        self._send_host = "tcp://127.0.0.1" + argv[4]
        self._cb_host = "tcp://127.0.0.1" + argv[5]
        self._stub_f = None
        self._cb_f = None
        KctlLogger.init()

        service = package.split('.')[-1]

        print(f'Initializing "{service}"')

    class Message:
        """Class to hold key word arguments for sending via protobuf"""
        __slots__ = ['kwargs']

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class STOP:
        """Class to break stub/callback push/pull"""
        __slots__ = []

    def stub(self, f):
        self._stub_f = f
        return self._stub

    def callback(self, f):
        self._cb_f = f
        return self._callback

    def _protofy(self, msg, proto):
        """Checks whether the type is Message else it assumes it's a proto"""
        return proto(**msg.kwargs) if type(msg) == self.Message else msg

    def _check_rcv_proto(self, proto):
        pass

    def _check_send_proto(self, proto):
        pass

    def _check_cb_proto(self, proto):
        pass

    def _stub(self, msg):

        proto = self._protofy(msg, self._rcv_proto)
        self._check_rcv_proto(proto)
        msg = self._stub_f(proto)

        if msg is not None:
            raise ValueError('Send stub must return...')

        proto = self._send_proto(**msg.kwargs)
        self._check_send_proto(proto)
        body = proto.SerializeToString()
        return body

    def _callback(self, msg):
        proto = self._protofy(msg, self._cb_proto)
        self._check_cb_proto(proto)
        self._cb_f(proto)

    def _push_pull(self, func, push_host=None, pull_host=None):
        """Executes a push pull loop, executing the func as a callback

        :param func: callback to execute message with
        """
        push = True if push_host is not None else False
        pull = True if pull_host is not None else False

        if push:
            push_socket = self._context.socket(zmq.PUSH)
            push_socket.connect(push_socket)
            print('Socket created on ' + push_socket)

        if pull:
            pull_socket = self._context.socket(zmq.PULL)
            pull_socket.connect(pull_socket)
            print('Socket created on ' + pull_socket)

        while True:
            if pull:
                msg = pull_socket.recv()
                body = func(msg)
            else:
                body = func()
            if push:
                push_socket.send(body)

    def run(self, subs=None):
        """Takes optional sub functions to run in separate threads

        :param subs: iterable of functions
        """
        threads = []

        if subs is not None:
            for sub in subs:
                t = Thread(target=sub)
                t.start()
                threads.append(t)

        if self._send_host is not None or self._rcv_host is not None:
            t = Thread(
                target=self._push_pull,
                args=[self._stub],
                kwargs={
                    'push_host': self._send_host,
                    'pull_host': self._rcv_host
                }
            )
            t.start()
            threads.append(t)

        if self._cb_host:
            t = Thread(
                target=self._push_pull,
                args=[self._callback],
                kwargs={
                    'pull_host': self._cb_host
                }
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
