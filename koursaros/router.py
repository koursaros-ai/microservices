
from .network import Network, Route, SocketType, FLASK_PORT, Command
from flask import Flask, request, jsonify
from kctl.logger import set_logger
from .messages import Messages, MsgType
import json


class Router:
    """
    The router serves as an endpoint as a client. It receives
    requests from the client to send to the loop starting
    from a specific loop. It then redirects the network through it.
    """

    def __init__(self):
        # set logger
        self.logger = set_logger('router')
        self.logger.info('Initializing router')

        # set zeromq
        self.net = Network('router')
        self.net.build_socket(SocketType.PULL_CONNECT, Route.IN, name='ROUTER')
        self.net.build_socket(SocketType.PUSH_CONNECT, Route.OUT, name='ROUTER')

        # setup messages
        self.msgs = Messages()
        self.msg_count = 0
        self.statuses = dict()

    def send_msg(self, msg):
        self.msg_count += 1

        # use message count if no id is found in data
        msg_id = msg.pop('id') if 'id' in msg else self.msg_count
        msg = self.msgs.cast(msg, MsgType.JSON, MsgType.JSONBYTES)
        self.net.send(Route.OUT, Command.SEND, msg_id, msg)

    def get_res(self):
        # wait for response from service
        cmd, msg_id, msg = self.net.recv(Route.IN)
        res = json.loads(msg)
        res['id'] = msg_id

        if cmd == Command.STATUS:
            self.statuses.update(msg)
            return self.get_res()

        elif cmd == Command.ERROR:
            res['status'] = 'failure'
            return res

        elif cmd == Command.SEND:
            res['status'] = 'success'
            return res

    def create_flask_app(self):
        app = Flask(__name__)
        router = self

        @app.route('/status', methods=['GET'])
        def status():
            return jsonify(router.statuses)

        @app.route('/send', methods=['POST'])
        def send():
            data = request.form if request.form else request.json
            router.logger.bold('Sending %s' % data)
            router.send_msg(data)
            res = router.get_res()
            return jsonify(res)

        return app

    def run(self):
        app = self.create_flask_app()
        self.logger.info('Starting flask on port %s' % FLASK_PORT)
        app.run(port=FLASK_PORT, threaded=True, host='0.0.0.0')


if __name__ == "__main__":
    r = Router()
    r.run()
