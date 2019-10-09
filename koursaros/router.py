
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from .network import Network, Route, SocketType, Command, FLASK_PORT, POLL_TIMEOUT
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
        self.services = sys.argv[1:]
        self.logger = set_logger('router')
        self.logger.info(f'Initializing "router"')

        # set zeromq
        self.net = Network()
        self.net.build_socket(SocketType.PULL_BIND, Route.CTRL)
        self.msg_count = 0
        self.poller = zmq.Poller()

    def bind(self, service):
        """
        Bind the desired service to send incoming messages
        to the router instead of the next service.
        The router will send json versions of the protobuf.
        """
        self.net.build_socket(SocketType.PUSH_CONNECT, Route.OUT, name=service)
        self.net.send(Route.OUT, Command.BIND, 0, b'')

        route_out = self.net.sockets[Route.OUT]
        self.poller.register(route_out, zmq.POLLIN)

        socks = dict(self.poller.poll(POLL_TIMEOUT))

        if route_out in socks and socks[route_out] == zmq.POLLIN:
            return self.net.recv(Route.CTRL).recv()[0] # get ack

    def send_msg(self, dict_):
        self.msg_count += 1

        # use message count if no id is found in data
        msg_id = dict_.pop('id') if 'id' in dict_ else self.msg_count
        msg = json.dumps(dict_).encode()
        self.net.send(Route.OUT, Command.BIND, msg_id, msg)

        # wait for response from service
        _, msg_id, msg = self.net.recv(Route.CTRL)
        res = json.loads(msg)

        res['id'] = msg_id
        return res

    def create_flask_app(self):
        app = Flask(__name__)
        router = self

        @app.route('/send')
        def receive():
            if Route.OUT not in self.net.sockets:
                first_service = router.services[-1]
                cmd = router.bind(first_service)

                if cmd != Command.ACK:
                    return jsonify(dict(status='failure', msg='{} did not respond'
                                        .format(first_service)))

            data = request.form if request.form else request.json
            res = router.send_msg(data)
            return jsonify(res)

        return app

    def run(self):
        app = self.create_flask_app()
        self.logger.info('Starting flask on port %s' % FLASK_PORT)
        app.run(port=FLASK_PORT, threaded=True, host='0.0.0.0')


if __name__ == "__main__":
    r = Router()
    r.run()
