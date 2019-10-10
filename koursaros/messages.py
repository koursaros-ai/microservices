
from google.protobuf.json_format import MessageToJson, Parse as JsonToMessage
from grpc_tools import protoc
from enum import Enum
import json


class MsgType(Enum):
    RECV_PROTO = 0
    SEND_PROTO = 1
    PROTOBYTES = 2
    JSON = 3
    JSONBYTES = 4
    KWARGS = 5


class Messages:
    def __init__(self, proto_module=None, send_proto=None, recv_proto=None):
        if proto_module:
            self.compile_protobufs(proto_module)
            self.protos = __import__('messages_pb2')

            self.recv_proto = getattr(self.protos, recv_proto)
            self.send_proto = getattr(self.protos, recv_proto)

    def cast(self, msg, from_type: 'MsgType', to_type: 'MsgType'):

        if from_type == MsgType.JSONBYTES and to_type == MsgType.RECV_PROTO:
            proto = self.recv_proto()
            JsonToMessage(msg, proto)
            return proto

        elif from_type in (MsgType.RECV_PROTO, MsgType.SEND_PROTO) and to_type == MsgType.JSONBYTES:
            return MessageToJson(msg)

        elif from_type == MsgType.PROTOBYTES and to_type == MsgType.RECV_PROTO:
            proto = self.send_proto()
            proto.ParseFromString(msg)
            return proto

        elif from_type == MsgType.SEND_PROTO and to_type == MsgType.PROTOBYTES:
            proto = msg.SerializeToString()
            return proto

        elif from_type == MsgType.JSON and to_type == MsgType.JSONBYTES:
            return json.dumps(msg).encode()

        elif from_type == MsgType.KWARGS and to_type == MsgType.SEND_PROTO:
            return self.send_proto(**msg)

        else:
            raise NotImplementedError

    @staticmethod
    def protobuf_fields(proto):
        return proto.__name__, list(proto.DESCRIPTOR.fields_by_name)

    @property
    def specs(self):
        recv_name, recv_fields = self.protobuf_fields(self.recv_proto)
        send_name, send_fields = self.protobuf_fields(self.send_proto)

        return {'recv: "%s"' % recv_name: recv_fields, 'SEND: "%s' % send_name: send_fields}

    @staticmethod
    def compile_protobufs(path):
        protoc.main((
            '',
            '-I=%s' % path,
            '--python_out=%s' % path,
            '%s/messages.proto' % path,
        ))