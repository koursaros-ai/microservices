
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from .helpers import *
import json
import zmq
import sys


class Router:
    """
    The router serves as an endpoint as a client. It receives
    requests from the client to send to the loop starting
    from a specific loop. It then redirects the network through it.
    """

    def __init__(self):
        # set logger
        cmd = sys.argv
        verbose = True if '--verbose' in cmd else False
        if verbose: cmd.remove('--verbose')
        self.services = cmd[1:]
        self.logger = set_logger('router', verbose=verbose)
        self.logger.info(f'Initializing "router", verbose: %s' % verbose)

        # set zeromq
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.PULL)
        self.service_socket = None
        self.msg_count = 0
        self.poller = zmq.Poller()

    def connect_service_socket(self, service):
        _, service_port = get_hash_ports(service, 2)
        service_address = HOST % service_port
        self.service_socket = self.context.socket(zmq.PUSH)
        self.logger.bold('Connecting PUSH socket to {}'
                         .format(service_address))
        self.service_socket.connect(service_address)

    def send_service_command(self, command):
        cmd = _pack_msg(command, 0, b'')
        self.service_socket.send(cmd)

    def bind(self, service):
        """
        Bind the desired service to send incoming messages
        to the router instead of the next service.
        The router will send json versions of the protobuf.
        """
        self.connect_service_socket(service)
        self.send_service_command(RouterCmd.BIND)
        self.poller.register(self.service_socket, zmq.POLLIN)

        socks = dict(self.poller.poll(POLL_TIMEOUT))

        if self.service_socket in socks and socks[self.service_socket] == zmq.POLLIN:
            return _unpack_msg(self.router_socket.recv())

    def send_msg(self, dict_):
        self.msg_count += 1

        # use message count if no id is found in data
        msg_id = dict_.pop('id') if 'id' in dict_ else self.msg_count
        msg = _pack_msg(RouterCmd.SEND, msg_id, json.dumps(dict_).encode())
        self.service_socket.send(msg)

        # wait for response from service
        body = self.router_socket.recv()
        _, msg_id, msg = _unpack_msg(body)
        res = json.loads(msg)

        res['id'] = msg_id
        return res

    def create_flask_app(self):
        app = Flask(__name__)
        router = self

        @app.route('/send')
        def receive():
            if router.service_socket is None:
                first_service = router.services[-1]
                res = router.bind(first_service)

                if res[0] != RouterCmd.ACK:
                    return jsonify(dict(status='failure', msg='{} did not respond'
                                        .format(first_service)))

            data = request.form if request.form else request.json
            res = router.send_msg(data)
            return jsonify(res)

        return app

    def run(self):
        self.router_socket.bind(ROUTER_ADDRESS)
        self.logger.bold('PULL socket connected on %s' % ROUTER_ADDRESS)

        app = self.create_flask_app()
        self.logger.info('Starting flask on port %s' % FLASK_PORT)
        app.run(port=FLASK_PORT, threaded=True, host='0.0.0.0')


if __name__ == "__main__":
    r = Router()
    r.run()
