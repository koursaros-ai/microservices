
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from .helpers import *
from enum import Enum
import json
import zmq
import sys


class RouterCmd(Enum):
    SEND = b'1'
    BIND = b'2'
    RESET = b'3'


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
        self.services = sys.argv[1:]

        # set zeromq
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.PUSH)
        self.service_socket = None

    def connect_service_socket(self, service):
        service_port, _ = get_hash_ports(service, 2)
        service_address = HOST % service_port
        self.service_socket = self.context.socket(zmq.PUSH)
        self.service_socket.connect(service_address)

    def send_service_command(self, command):
        self.service_socket.send(command.value + _int_to_16byte(0))

    def bind(self, service):
        """
        Bind the desired service to send incoming messages
        to the router instead of the next service.
        The router will send json versions of the protobuf.
        """
        if self.service_socket is not None:
            self.send_service_command(RouterCmd.RESET)
            self.service_socket.close()

        self.connect_service_socket(service)
        self.send_service_command(RouterCmd.BIND)

        # wait for response from service
        return self.router_socket.recv()

    def send_msg(self, dict_):
        msg_id = _int_to_16byte(dict_.pop('id'))
        self.service_socket.send(RouterCmd.SEND.value + msg_id + json.dumps(dict_).encode())

        # wait for response from service
        body = self.router_socket.recv()
        _, msg_id, msg = _parse_msg(body)
        res = json.loads(msg)
        res['id'] = _16byte_to_int(msg_id)
        return res

    def create_flask_app(self):
        app = Flask(__name__)
        router = self

        @app.route('/bind')
        def bind():
            res = router.bind(router.services[0])
            return jsonify(dict(status='success', msg=res))

        @app.route('/send')
        def receive():
            data = request.form if request.form else request.json
            res = router.send_msg(json.loads(data))
            return jsonify(res)

        return app

    def run(self):
        self.router_socket.bind(ROUTER_ADDRESS)
        self.logger.bold('PUSH socket connected on %s' % ROUTER_ADDRESS)

        app = self.create_flask_app()
        self.logger.info('Starting flask on port %s' % FLASK_PORT)
        app.run(port=FLASK_PORT, threaded=True, host='0.0.0.0')


if __name__ == "__main__":
    r = Router()
    r.run()
