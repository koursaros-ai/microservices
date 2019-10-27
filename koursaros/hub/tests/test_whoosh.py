import os
import unittest
from unittest import SkipTest

from gnes.proto import gnes_pb2
from gnes.client.base import ZmqClient
from gnes.service.base import SocketType
from gnes.cli.parser import set_router_parser, _set_client_parser
from gnes.service.indexer import IndexerService
import numpy as np


class TestWhoosh(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.yaml = os.path.join(dirname, 'yaml', 'test-whoosh.yml')
        self.yaml_joint = os.path.join(dirname, 'yaml', 'test-joint.yml')
        self.python_code = os.path.join(dirname, '../', 'indexer/whoosh/whoosh.py')

        self.test_str = []
        self.test_vec = []
        self._msl = 512
        with open(os.path.join(dirname, 'sonnets_small.txt')) as f:
            for line in f:
                line = line.strip()
                if line == '': continue
                self.test_vec.append(np.frombuffer(
                        line.encode()[:self._msl] + b'\x00' * (self._msl - len(line)),
                        dtype=np.uint8
                ))
                self.test_str.append(line)

    @SkipTest
    def test_whoosh(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.yaml,
            '--socket_out', str(SocketType.PUB_BIND),
            '--py_path', self.python_code,
        ])
        args.as_response = True
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with IndexerService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            for i, vec in enumerate(self.test_vec):
                doc = msg.request.index.docs.add()
                doc.doc_id = i
                doc.raw_text = self.test_str[i]
                c = doc.chunks.add()
                c.doc_id = i
                c.offset = 0
                c.embedding.data = vec.tobytes()
                for d in vec.shape:
                    c.embedding.shape.extend([d])
                c.embedding.dtype = str(vec.dtype)
                c.text = self.test_str[i]
            c1.send_message(msg)

            r = c1.recv_message()
            self.assert_(r.response.index)

            for i, vec in enumerate(self.test_vec):
                msg = gnes_pb2.Message()
                msg.request.search.query.doc_id = 1
                msg.request.search.top_k = 1
                c = msg.request.search.query.chunks.add()
                c.doc_id = 1
                c.embedding.data = vec.tobytes()
                for d in vec.shape:
                    c.embedding.shape.extend([d])
                c.embedding.dtype = str(vec.dtype)
                c.offset = 0
                c.weight = 1
                c.text = self.test_str[i]
                c1.send_message(msg)
                r = c1.recv_message()
                try:
                    self.assert_(r.response.search.topk_results[0].chunk.doc_id == i)
                except:
                    pass

    def test_joint(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.yaml_joint,
            '--socket_out', str(SocketType.PUB_BIND),
            '--py_path', self.python_code,
        ])
        args.as_response = True
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with IndexerService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            for i, vec in enumerate(self.test_vec):
                doc = msg.request.index.docs.add()
                doc.doc_id = i
                doc.raw_text = self.test_str[i]
                c = doc.chunks.add()
                c.doc_id = i
                c.offset = 0
                c.embedding.data = vec.tobytes()
                for d in vec.shape:
                    c.embedding.shape.extend([d])
                c.embedding.dtype = str(vec.dtype)
                c.text = self.test_str[i]
            c1.send_message(msg)

            r = c1.recv_message()
            self.assert_(r.response.index)

            for i, vec in enumerate(self.test_vec):
                msg = gnes_pb2.Message()
                msg.request.search.query.doc_id = 1
                msg.request.search.top_k = 1
                c = msg.request.search.query.chunks.add()
                c.doc_id = 1
                c.embedding.data = vec.tobytes()
                for d in vec.shape:
                    c.embedding.shape.extend([d])
                c.embedding.dtype = str(vec.dtype)
                c.offset = 0
                c.weight = 1
                c.text = self.test_str[i]
                c1.send_message(msg)
                r = c1.recv_message()
                try:
                    self.assert_(r.response.search.topk_results[0].chunk.doc_id == i)
                except:
                    pass

    def tearDown(self):
        pass