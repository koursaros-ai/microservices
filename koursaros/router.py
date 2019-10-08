from koursaros.streamer import get_hash_ports
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from threading import Thread
import json
import zmq

HOST = "tcp://127.0.0.1:{}"
MSG_BASE = b'koursaros:'


class Router:
    """
    The router serves as an endpoint as a client. It receives
    requests from the client to send to the loop starting
    from a specific loop. It then redirects the network through it.
    """

    def __init__(self):
        # set logger
        self.logger = set_logger('router')
        self.logger.info(f'Initializing "router"')

        # set zeromq
        context = zmq.Context()
        in_port, out_port = get_hash_ports(service_name, 2)
        rcv_address = HOST.format(in_port)
        send_address = HOST.format(out_port)
        self.out_port = None

        self._pull_socket = context.socket(zmq.PULL)
        self._pull_socket.connect(rcv_address)
        self.logger.bold('PULL socket connected on %s' % rcv_address)
        self._push_socket = context.socket(zmq.PUSH)
        self._push_socket.connect(send_address)
        self.logger.bold('PUSH socket connected on %s' % send_address)
        self._stub_f = None
        self._cb_f = None

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

    def _rcv(self, msg, msg_tag=b''):
        """
        The stub receives a message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned

        :param msg: Service.Message, Proto Class, or binary message
        """
        proto = self._protofy(msg, self._rcv_proto_cls)
        self._check_rcv_proto(proto)

        self._send(proto, msg_tag)

    @classmethod
    def reroute(cls, service):
        cls.out_port, _ = get_hash_ports(service, 2)


    def expose(self):
        app = Flask(__name__)

        @app.route('/reroute')
        def reroute():
            data = request.form if request.form else request.json
            req = json.loads(data)
            service = req.pop('service')
            Router.reroute(service)

            return jsonify(dict(status='success', msg=queue.get()))

        @app.route('/')
        def receive():
            jso = request.args.get('q')
            req = json.loads(jso)
            msg_id = req.pop('id')


            return jsonify(dict(status='success', msg=queue.get()))

    def _send(self, proto, msg_tag):
        """
        Append the current service's msg tag if
        the message didn't come with one...

        :param proto: protobuf instance
        """
        self._push_socket.send(msg_tag + body)

    def _serve(self):
        """
        Receives the message body, parses the tag,
        and sends to _rcv
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
