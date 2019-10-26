import unittest
import os

from gnes.cli.parser import set_router_parser, _set_client_parser
from gnes.service.router import RouterService
from gnes.service.base import SocketType
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2


class TestBlock(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.rerank_router_yaml = os.path.join(dirname, '../', 'router/block/block_train.yml')
        self.python_code = os.path.join(dirname, '../', 'router/block/block.py')


        self.args = set_router_parser().parse_args([
            '--yaml_path', self.rerank_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND),
            '--py_path', self.python_code
        ])
        self.c_args = _set_client_parser().parse_args([
            '--port_in', str(self.args.port_out),
            '--port_out', str(self.args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])

    def test_block_router(self):
        with RouterService(self.args), ZmqClient(self.c_args) as c1:
            msg = gnes_pb2.Message()
            msg.request.train.docs.add()
            c1.send_message(msg)
            msg = gnes_pb2.Message()
            msg.request.index.docs.add()
            c1.send_message(msg)
            r = c1.recv_message()
