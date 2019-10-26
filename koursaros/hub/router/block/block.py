from gnes.router.base import BaseRouter
from gnes.proto import gnes_pb2
from gnes.service.base import BlockMessage
from typing import List


class BlockRouter(BaseRouter):
    """ :param block: runtimes to block"""

    def __init__(self, block: List[str] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block = block

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        """
        Log the incoming message
        :param msg: incoming message
        """

        runtime = getattr(msg, msg.WhichOneof('body')).WhichOneof('body')

        if runtime in self.block:
            self.logger.info('Blocking %s msg...' % runtime)
            raise BlockMessage
