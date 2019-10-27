from gnes.router.base import BaseRouter
from gnes.proto import gnes_pb2

class RespReqRouter(BaseRouter):
    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        """
        Log the incoming message
        :param msg: incoming message
        """

        runtime = getattr(msg, msg.WhichOneof('body')).WhichOneof('body')
        print('recieved msg')
        print(msg)
        print(runtime)
        if runtime == 'index':
            req = gnes_pb2.Message()