import os
import unittest

from gnes.proto import gnes_pb2
from gnes.client.base import ZmqClient
from gnes.service.base import SocketType
from gnes.cli.parser import set_router_parser, _set_client_parser
from gnes.service.router import RouterService



class TestReranker(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.model_path = os.path.join(dirname, 'model.bin')
        self.rerank_router_yaml = os.path.join(dirname, 'yaml', '')

        self.test_str = []
        with open(os.path.join(dirname, 'sonnets_small.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

    def test_rerank(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.rerank_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1, ZmqClient(c_args) as c2:
            for line in self.test_str:
                msg = gnes_pb2.Message()
                msg.request.index.docs.extend([gnes_pb2.Document(raw_text=line) for _ in range(5)])
                msg.envelope.num_part.extend([1, 3])
                c1.send_message(msg)
                c1.send_message(msg)
                c1.send_message(msg)
                r = c1.recv_message()
                self.assertSequenceEqual(r.envelope.num_part, [1])
                print(r.envelope.routes)

    def tearDown(self):
        if os.path.exists(self.model_path):
            os.remove(self.model_path)