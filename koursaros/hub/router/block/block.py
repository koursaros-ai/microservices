from gnes.router.base import BaseRouter
from gnes.proto import gnes_pb2
from gnes.service.base import BlockMessage
from typing import List


class BlockRouter(BaseRouter):
    """ :param block: runtimes to block"""

    def __init__(self, block: List[str] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)

        def block_if(runtime):
            if runtime in block:
                self.logger.info('Blocking %s msg...' % runtime)
                raise BlockMessage

        self.routes = {
            gnes_pb2.Request.TrainRequest: lambda: block_if('train'),
            gnes_pb2.Response.TrainResponse: lambda: block_if('train'),
            gnes_pb2.Request.IndexRequest: lambda: block_if('index'),
            gnes_pb2.Response.IndexResponse: lambda: block_if('index'),
            gnes_pb2.Request.QueryRequest: lambda: block_if('query'),
            gnes_pb2.Response.QueryResponse: lambda: block_if('query')
        }

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        """
        Log the incoming message
        :param msg: incoming message
        """
        self.routes[type(getattr(msg, msg.WhichOneof('body')))]()
