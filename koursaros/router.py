from koursaros.streamer import get_hash_ports
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from .helpers import _parse_msg, _int_to_16byte
from threading import Thread
from pathlib import Path
from .yamls import Yaml
from queue import Queue
import json
import zmq
import sys

HOST = "tcp://127.0.0.1:{}"
MSG_BASE = b'koursaros:'
ROUTER_PUSH_PORT = 49152


class Router:
    """
    The router serves as an endpoint as a client. It receives
    requests from the client to send to the loop starting
    from a specific loop. It then redirects the network through it.
    """
    in_port = None
    out_port = None
    expose_port = 5000
    pull_socket = None
    push_socket = None

    def __init__(self):
        # set yaml
        pipeline_yaml_path = Path(sys.argv[1])
        self.pipeline_yaml = Yaml(pipeline_yaml_path)

        # set logger
        self.logger = set_logger('router')
        self.logger.info(f'Initializing "router"')

        # set zeromq
        self.context = zmq.Context()
        send_address = HOST.format(ROUTER_PUSH_PORT)
        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.bind(send_address)

        self.logger.bold('PUSH socket connected on %s' % send_address)
        self.queues = dict()

    def _rcv(self, body):
        method, msg_id, msg = _parse_msg(body)
        self.queues[msg_id].put(msg)

    def reroute(self, service):
        # send to pull port of desired service
        self.out_port, _ = get_hash_ports(service, 2)
        self.service_socket = self.context.socket(zmq.PUSH)
        self.service_socket.send(b'RER' + _int_to_16byte(0))

        self._push_socket.connect(send_address)

    def expose(self):

        app = Flask(__name__)
        router = self

        @app.route('/reroute')
        def reroute():
            data = request.form if request.form else request.json
            req = json.loads(data)
            service = req.pop('service')
            router.reroute(service)

            return jsonify(dict(status='success'))

        @app.route('/')
        def receive():
            jso = request.args.get('q')
            req = json.loads(jso)
            msg_id = req.pop('id')
            queue = Queue()
            router.queues[msg_id] = queue
            return jsonify(dict(msg=queue.get()))

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
