
from google.protobuf.json_format import MessageToJson, Parse as JsonToMessage, ParseError
from json.decoder import JSONDecodeError
from koursaros.router import RouterCmd
from kctl.logger import set_logger
from traceback import format_exc
from koursaros.helpers import *
from grpc_tools import protoc
from .yamls import Yaml
import pathlib
import json
import sys
import zmq
import os


class Service:
    """The base service class"""

    def __init__(self):
        cmd = sys.argv
        verbose = True if '--verbose' in cmd else False
        if verbose: cmd.remove('--verbose')

        # set yamls
        yaml_path = pathlib.Path(cmd[1])
        self.yaml = Yaml(yaml_path)
        self.name = yaml_path.stem
        _base_dir_path = pathlib.Path(cmd[0]).parent
        self.base_yaml = Yaml(_base_dir_path.joinpath('base.yaml'))

        # set logger

        self.logger = set_logger(self.name, verbose=verbose)
        self.logger.info('Initializing "{}", verbose: {}'.format(self.name, verbose))

        # set directories
        os.chdir(_base_dir_path)
        sys.path.insert(1, str(_base_dir_path))

        # compile messages
        self._compile_messages_proto(_base_dir_path)
        messages = __import__('messages_pb2')
        self._rcv_proto_cls = messages.__dict__.get(self.base_yaml.rcv_proto)
        self._send_proto_cls = messages.__dict__.get(self.base_yaml.send_proto)

        # defaults
        self._stub_f = None
        self._bound = False
        self.push_socket = None
        self.pull_socket = None
        self.router_socket = None

    @property
    def default_addresses(self):
        in_port, out_port = get_hash_ports(self.name, 2)
        return HOST % in_port, HOST % out_port

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
        return

    def _send_to_stub(self, proto):
        # hand proto to stub
        returned = self._stub_f(proto)

        # cast returned type to proto
        if returned is None:
            raise ValueError('Send stub must return...')
        elif isinstance(returned, dict):
            return self._send_proto_cls(**returned)
        elif isinstance(returned, self._send_proto_cls):
            return returned
        else:
            raise TypeError('Cannot cast type "%s" to protobuf' % type(returned))

    def _send_to_router(self, msg_id, proto):
        msg = RouterCmd.PASS.value + msg_id + MessageToJson(proto)
        self.router_socket.send(msg)

    def _send_to_next_service(self, msg_id, proto):
        msg = RouterCmd.PASS.value + msg_id + proto.SerializeToString()
        self.push_socket.send(msg)

    def _send_error_to_router(self, msg_id, error):
        err = dict(status='failure', error=error)
        msg = RouterCmd.PASS.value + msg_id + json.dumps(err).encode()
        self.router_socket.send(msg)

    def _protofy_rcv_msg(self, msg):
        proto = self._rcv_proto_cls()
        proto.ParseFromString(msg)
        return proto

    def connect(self):
        # set zeromq
        context = zmq.Context()
        self.pull_socket = context.socket(zmq.PULL)
        self.push_socket = context.socket(zmq.PUSH)
        self.router_socket = context.socket(zmq.PUSH)

        rcv_address, send_address = self.default_addresses
        # pull
        self.pull_socket.connect(rcv_address)
        self.logger.bold('PULL socket connected on %s' % rcv_address)

        # push
        self.push_socket.connect(send_address)
        self.logger.bold('PUSH socket connected on %s' % send_address)

        # router
        self.router_socket.connect(ROUTER_ADDRESS)
        self.logger.bold('ROUTER socket connected on %s' % ROUTER_ADDRESS)

    def run(self):
        """
        The stub receives a message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned

        :param: binary message
        """
        self.connect()

        while True:
            body = self.pull_socket.recv()
            command, msg_id, msg = _parse_msg(body)
            self.logger.debug('Received cmd: {} | id: {} | msg: {}'
                              .format(command, msg_id, msg))

            if self._bound:
                if command == RouterCmd.RESET.value:
                    self.logger.debug('Acknowledging RESET request.')
                    self._bound = False

                elif command == RouterCmd.SEND.value:
                    try:
                        proto_in = JsonToMessage(msg, self._rcv_proto_cls)
                        proto_out = self._send_to_stub(proto_in)
                        self._send_to_next_service(msg_id, proto_out)
                    except ParseError as e:
                        self._send_error_to_router(msg_id, repr(e))
                    except TypeError as e:
                        self._send_error_to_router(msg_id, repr(e))
                    except ValueError as e:
                        self._send_error_to_router(msg_id, repr(e))
                    except:
                        self._send_error_to_router(msg_id, format_exc())

                # not sent from router and going to router
                elif command == RouterCmd.PASS.value:
                    proto_in = self._protofy_rcv_msg(msg)
                    self._send_to_router(msg_id, proto_in)

            else:
                if command == RouterCmd.BIND.value:
                    self._bound = True
                    self.logger.debug('Acknowledging BIND request.')
                    self.router_socket.send(b'%s acknowledged.' % self.name.encode())

                # not sent from router and not going to router
                elif command == RouterCmd.PASS.value:
                    proto_in = self._protofy_rcv_msg(msg)
                    proto_out = self._send_to_stub(proto_in)
                    self._send_to_next_service(msg_id, proto_out)




