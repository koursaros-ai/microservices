
from google.protobuf.json_format import MessageToJson, Parse as JsonToMessage, ParseError
from kctl.logger import set_logger
from traceback import format_exc
from .network import Network, Route, SocketType, Command
from grpc_tools import protoc
from .yamls import Yaml
import pathlib
import sys
import os


class Service:
    """The base service class"""

    def __init__(self):

        # set yamls
        yaml_path = pathlib.Path(sys.argv[1])
        self.yaml = Yaml(yaml_path)
        self.name = yaml_path.stem
        _base_dir_path = pathlib.Path(sys.argv[0]).parent
        self.base_yaml = Yaml(_base_dir_path.joinpath('base.yaml'))

        # set logger
        self.logger = set_logger(self.name)
        self.logger.info('Initializing "{}"')

        # set directories
        os.chdir(_base_dir_path)
        sys.path.insert(1, str(_base_dir_path))

        # compile messages
        self._compile_protobufs(_base_dir_path)
        messages = __import__('messages_pb2')
        self.recv_proto = getattr(messages, self.base_yaml.recv_proto)
        self.send_proto = getattr(messages, self.base_yaml.send_proto)

        # defaults
        self._stub_f = None
        self._bound = False

    @staticmethod
    def protobuf_fields(proto):
        return proto.__name__, list(proto.DESCRIPTOR.fields_by_name)

    @property
    def specs(self):
        recv_name, recv_fields = self.protobuf_fields(self.recv_proto)
        send_name, send_fields = self.protobuf_fields(self.send_proto)

        return {'recv: "%s"' % recv_name: recv_fields, 'SEND: "%s' % send_name: send_fields}

    def _compile_protobufs(self, path):
        self.logger.info(f'Compiling messages for "{path}"...')

        protoc.main((
            '',
            f'-I={path}',
            f'--python_out={path}',
            f'{path}/messages.proto',
        ))

    def stub(self, f):
        self._stub_f = f

    def _stub(self, proto):
        # hand proto to stub
        returned = self._stub_f(proto)

        # cast returned type to proto
        if returned is None:
            raise ValueError('Send stub must return...')
        elif isinstance(returned, dict):
            return self.send_proto(**returned)
        elif isinstance(returned, self.send_proto):
            return returned
        else:
            raise TypeError('Cannot cast type "%s" to protobuf' % type(returned))

    def run(self):
        """
        The stub receives a message and casts it into a proto
        for the stub to receive. Whatever the stub returns is checked
        and then returned
        """
        net = Network()
        net.build_socket(SocketType.PULL_CONNECT, Route.IN, name=self.name)
        net.build_socket(SocketType.PUSH_CONNECT, Route.OUT, name=self.name)
        net.build_socket(SocketType.PUSH_CONNECT, Route.CTRL, name=self.name)

        while True:
            net = Network()
            cmd, msg_id, msg = net.sockets[Route.IN].recv()

            if self._bound:
                if cmd == Command.SEND:
                    try:
                        proto_in = self.recv_proto()
                        JsonToMessage(msg, proto_in)
                        proto_out = self._stub(proto_in)
                        msg = proto_out.SerializeToString()
                        net.sockets[Route.OUT].send(Command.PASS, msg_id, msg)
                    except ParseError as e:
                        net.sockets[Route.CTRL].send(Command.PASS, msg_id, repr(e).encode())
                    except TypeError as e:
                        net.sockets[Route.CTRL].send(Command.PASS, msg_id, repr(e).encode())
                    except ValueError as e:
                        net.sockets[Route.CTRL].send(Command.PASS, msg_id, repr(e).encode())
                    except:
                        net.sockets[Route.CTRL].send(Command.PASS, msg_id, format_exc().encode())

                # not sent from router and going to router
                elif cmd == Command.PASS:
                    proto = self.recv_proto()
                    proto.ParseFromString(msg)
                    msg = MessageToJson(proto).encode()
                    net.sockets[Route.CTRL].send(Command.PASS, msg_id, msg)

            else:
                if cmd == Command.BIND:
                    self._bound = True
                    net.sockets[Route.CTRL].send(Command.ACK, msg_id, msg)

                # not sent from router and going to next service
                elif cmd == Command.BIND:
                    proto_in = self.recv_proto()
                    proto_in.ParseFromString(msg)
                    proto_out = self._stub(proto_in)
                    msg = proto_out.SerializeToString()
                    net.sockets[Route.OUT].send(Command.PASS, msg_id, msg)




