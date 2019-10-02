from kctl.logger import KctlLogger
from kctl.cli import get_args
from threading import Thread
from inspect import isclass
from random import randint
from inspect import stack
import functools
import pika
import time

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class ActivatingContainer:
    """Class that holds a number of other classes.
    Class names are designated in __names__

    When initialized, the container sets
    __active__ (boolean) to each subclass depending on whether
    the class is in active_names then initializes them
    with *args and **kwargs.

    Also sets the container __active__ to true if any
    children are active...

    Also stores a reference to each active subclass.
    """

    __names__ = []
    __active__ = False
    __activerefs__ = []

    def __init__(self, active_names, *args, **kwargs):
        for cls in list(self):
            cls_name = cls.__class__.__name__
            __active__ = True if cls_name in active_names else False
            setattr(cls, '__active__', __active__)

            instance = cls(*args, **kwargs)
            setattr(self, cls_name, instance)

            if __active__:
                self.__active__ = True
                self.__activerefs__.append(instance)

    def __iter__(self):
        attrs = []

        for name in self.__names__:
            attrs.append(getattr(self, name))

        self.iter = iter(attrs)
        return self

    def __next__(self):
        return next(self.iter)

    def __len__(self):
        return len(self.__names__)

    def randomactive(self):
        rand_int = randint(0, len(self.__activerefs__) - 1)
        return self.__activerefs__[rand_int]


class Pipeline:
    """The pipeline object holds services (.services), connection
    parameters (.connections), and command line arguments (.args)

    :param package: __package__ parameter
    :param prefetch: (from pika) Specifies a prefetch window in terms of whole
        messages. This field may be used in combination with the
        prefetch-size field; a message will only be sent in advance
        if both prefetch windows (and those at the channel and connection
        level) allow it. The prefetch-count is ignored by consumers
        who have enabled the no-ack option.
    """

    class _Connections(ActivatingContainer):
        pass

    class _Services(ActivatingContainer):
        pass

    def __init__(self, package, prefetch=1):
        # predicts the active service from file path
        self.args = get_args()
        self.prefetch = prefetch

        active_connection_name = self.args.connection
        self.connections = self._Connections([active_connection_name])
        self.active_connection = getattr(self.connections, active_connection_name)

        active_service_name = None if package is None else package.split('.')[-1]

        # init services with reference to pipeline
        self.services = self._Services([active_service_name], self)
        self.active_service = getattr(self.services, active_service_name)
        KctlLogger.init(active_connection_name + '.' + active_service_name)





class Connection:
    pass


class Service:
    """The pipeline object holds stubs (.stubs)

    :param _pipe: Pipeline object reference
    """
    __active__ = False

    class _Stubs(ActivatingContainer):
        pass

    def __init__(self, _pipe):

        self._pipe = _pipe
        active_stub_names = self._Stubs.__names__ if self.__active__ else []

        # init stubs with reference to pipeline and service
        self.stubs = self._Stubs(active_stub_names, _pipe, self)

        # set stub with refs to each other
        for stub in self.stubs:
            import pdb; pdb.set_trace()
            stub.set_out_stub()

    def run(self):
        for stub in self.stubs:
            stub.run()
        for stub in self.stubs:
            stub.join()


class Stub:
    __active__ = False
    _out_stub = None
    _InProto = None
    _OutProto = None
    _should_send = False
    connection = None
    channel = None
    run_threads = None
    process_thread = None

    def __init__(self, _pipe, _service):
        self._name = self.__class__.__name__
        self._pipe = _pipe
        self._service = _service

    def __call__(self, func):
        if not self.__active__:
            self.raise_not_active()

        self.func = func

    class NotInActiveServiceError(Exception):
        pass

    class NoReturnError(Exception):
        pass

    class ShouldNotReturnError(Exception):
        pass

    class WrongProtoTypeError(Exception):
        pass

    def raise_invalid_proto_out(self, correct_type, incorrect_type):
        msg = (f'Attemped to send "{correct_type}" to "{self._out_stub.__name__}"'
               f'... which expects "{incorrect_type}" message')
        raise self.WrongProtoTypeError(msg)

    def raise_not_active(self):
        # if the parent service is not active then crash
        msg = (f'Cannot use stubs from "{self._service.__name__}"'
               f'service in "{self._pipe.active}" service')
        raise self.NotInActiveServiceError(msg)

    def raise_no_return(self):
        msg = (f'"{self._name}" stub did not return anything,'
               f'but it should be sending to "{self._out_stub.__name__}" stub')
        raise self.NoReturnError(msg)

    def raise_should_not_return(self):
        msg = f'"{self._name}" stub should not return anything...'
        raise self.ShouldNotReturnError(msg)

    def set_out_stub(self):
        if self._out_stub is not None:
            for service in self._pipe.services:
                for stub in service.stubs:
                    if stub.__name__ == self._out_stub.__name__:
                        self._out_stub = stub

            self._should_send = True

    def process(self, proto, method):
        returned = self.func(proto)

        if self._should_send:
            if returned is None:
                self.raise_no_return()

            else:
                self.send(returned)

        else:
            if returned is not None:
                self.raise_should_not_return()

        self.ack_callback(method.delivery_tag)

    def send(self, proto):
        if self.__active__:
            self.publish_callback(proto)

        # if the stub is not in the current service then send to it
        else:
            # if stub is not active then find a random
            stub = self._pipe.active_service.stubs.randomactive()
            stub.publish_callback(proto)

    def check_proto_type(self, proto):
        correct_proto_type = self._OutProto.__name__
        checking_proto_type = proto.__class__.__name__

        if correct_proto_type != checking_proto_type:
            self.raise_invalid_proto_out(correct_proto_type, checking_proto_type)

    def publish(self, proto):
        self.check_proto_type(proto)
        body = proto.SerializeToString()

        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=self._out_stub.__name__,
            body=body,
            properties=PROPS
        )

    def publish_callback(self, proto):
        cb = functools.partial(self.publish, proto)
        self.connection.add_callback_threadsafe(cb)

    def consume(self):
        conn = self._pipe.connections.randomactive()

        credentials = pika.credentials.PlainCredentials(
            self._service.__name__, conn.password)
        params = pika.ConnectionParameters(
            conn.host, conn.port, self._pipe.__name__, credentials)

        while True:
            try:
                self.connection = pika.BlockingConnection(parameters=params)
                self.channel = self.connection.channel()
                break
            except Exception as exc:
                print(f'Failed pika connection...\n{exc.args}')
                time.sleep(RECONNECT_DELAY)

        self.channel.basic_qos(prefetch_count=self._pipe.prefetch)
        queue = self._service.__name__ + '.' + self.__name__
        cb = functools.partial(self.consume_callback)
        self.channel.basic_consume(queue=queue, on_message_callback=cb)
        print(f'Listening on {queue}...')
        self.channel.start_consuming()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self.channel.basic_ack, delivery_tag)
        self.connection.add_callback_threadsafe(cb)

    def consume_callback(self, channel, method, properties, body):
        proto = self._InProto()
        proto.ParseFromString(body)

        self.process_thread = Thread(target=self.process, args=(proto, method))
        self.process_thread.run()

    def run(self):
        t = Thread(target=self.consume)
        print(f'Running stub "{self.__name__}" {t.getName()}')
        t.start()
        self.run_threads.append(t)

    def join(self):
        for t in self.run_threads:
            print(f'Waiting for stub "{self.__name__}" to finish {t.getName()}')
            t.join()
