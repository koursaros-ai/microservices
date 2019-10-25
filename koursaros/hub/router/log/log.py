
from gnes.router.base import BaseRouter


class LogRouter(BaseRouter):
    """ Base class for the router. Inherit from this class to create a new router.
    Router forwards messages between services. Essentially, it receives a 'gnes_pb2.Message'
    and call `apply()` method on it.
    """

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        """
        Log the incoming message
        :param msg: incoming message
        """
        self.logger.info(msg)
