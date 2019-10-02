from threading import Thread, get_ident
from kctl.logger import KctlLogger
from kctl.cli import get_args
from random import randint
from queue import Queue
import functools
import pika


EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class ReprClassName:
    def __repr__(self):
        return self.__class__.__name__


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
            cls_name = cls.__name__
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

        return iter(attrs)

    def __len__(self):
        return len(self.__names__)

    def randomactive(self):
        rand_int = randint(0, len(self.__activerefs__) - 1)
        return self.__activerefs__[rand_int]


class Pipeline(ReprClassName):
    """The pipeline object holds services (.Services), connection
    parameters (.Connections), and command line arguments (.args)

    :param package: __package__ parameter
    :param prefetch: (from pika) Specifies a prefetch window in terms of whole
        messages. This field may be used in combination with the
        prefetch-size field; a message will only be sent in advance
        if both prefetch windows (and those at the channel and connection
        level) allow it. The prefetch-count is ignored by consumers
        who have enabled the no-ack option.
    """

    class Connections(ActivatingContainer):
        pass

    class Services(ActivatingContainer):
        pass

    def __init__(self, package, prefetch=1):
        print(f'Initializing "{repr(self)}"...')

        # predicts the active service from file path
        self.args = get_args()
        self.prefetch = prefetch

        active_connection_name = self.args.connection
        self.Connections = self.Connections([active_connection_name])
        self.active_connection = getattr(self.Connections, active_connection_name)

        if package is None:
            active_service_name = None
            self.active_service = None
        else:
            active_service_name = package.split('.')[-1]

        if self.args.debug:
            print(f'Initializing {self}.Services')

        # init services with reference to pipeline
        self.Services = self.Services([active_service_name], self)

        if package is not None:
            self.active_service = getattr(self.Services, active_service_name)
            KctlLogger.init()

        # set stub with refs to each other
        for Service in self.Services:
            for Stub in Service.Stubs:
                Stub.set_out_stub()


class Connection(ReprClassName):
    pass


class Service(ReprClassName):
    """The pipeline object holds stubs (.Stubs)

    :param _pipe: Pipeline object reference
    """
    __active__ = False

    class Stubs(ActivatingContainer):
        pass

    def __init__(self, _pipe):
        if _pipe.args.debug:
            print(f'Initializing "{self}" service...')

        self._pipe = _pipe
        active_stub_names = self.Stubs.__names__ if self.__active__ else []

        # init stubs with reference to pipeline and service
        self.Stubs = self.Stubs(active_stub_names, self)

    def run(self):
        for Stub in self.Stubs:
            Stub.run()
        for Stub in self.Stubs:
            Stub.join()


class Stub(ReprClassName):
    __active__ = False
    _out_stub = None
    _OutStub = None
    _in_proto = None
    _InProto = None
    _out_proto = None
    _OutProto = None
    _should_send = False

    _consumer = None
    _publisher = None

    _pthread = []
    _cthread = None

    def __init__(self, _service):

        self._pipe = _service._pipe
        self._service = _service

        if self._pipe.args.debug:
            print(f'Initializing "{self}" stub...')

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

    class WrongMessageTypeError(Exception):
        pass

    class StubNotFoundError(Exception):
        pass

    def raise_wrong_msg_type(self, incorrect_type):
        msg = (f'"{repr(self)}" sending "{incorrect_type}" message,'
               f'but {repr(self._OutStub)} expects "{self._OutStub._in_proto}" message')
        raise self.WrongMessageTypeError(msg)

    def raise_stub_not_found(self):
        msg = f'{repr(self)} could not find "{self._out_stub}" stub to send to'
        raise self.StubNotFoundError(msg)

    def raise_not_active(self):
        # if the parent service is not active then crash
        msg = (f'Cannot use stubs from "{self._service}"'
               f'service in "{self._pipe.active}" service')
        raise self.NotInActiveServiceError(msg)

    def raise_no_return(self):
        msg = (f'"{self}" stub did not return anything,'
               f'but it should be sending to "{self._out_stub}" stub')
        raise self.NoReturnError(msg)

    def raise_should_not_return(self):
        msg = f'"{self}" stub should not return anything...'
        raise self.ShouldNotReturnError(msg)

    def set_out_stub(self):
        if self._out_stub is not None:

            for Service in self._pipe.Services:
                for Stub in Service.Stubs:
                    if repr(Stub) == self._out_stub:
                        self._OutStub = Stub

            self._should_send = True

            if self._OutStub is None:
                self.raise_stub_not_found()

            if self._out_proto != self._OutStub._in_proto:
                self.raise_wrong_msg_type(self._out_proto)

    def process(self, proto, method=None):
        debug = self._pipe.args.debug
        if debug:
            print(f'"{self}" stub processing "{proto.__class__.__name__}"...')

        returned = self.func(proto)

        if debug:
            print(f'"{self.func.__name__}" returned "{returned.__class__.__name__}"...')

        if self._should_send:
            if returned is None:
                self.raise_no_return()

            else:
                self.send(returned)

        else:
            if returned is not None:
                self.raise_should_not_return()
        if method is not None:
            tag = method.delivery_tag
            if debug:
                print(f'"{self}" stub sending ack callback: {tag}')
            self._consumer.ack_callback(tag)

    def send(self, proto):

        if self._pipe.args.debug:
            not_ = '' if self.__active__ else 'not '
            print(f'"{self}" is {not_}active...')

        if self.__active__:
            self._publisher.publish_callback(proto)

        # if the stub is not in the current service then send to it
        else:
            # if stub is not active then find a random
            stub = self._pipe.active_service.Stubs.randomactive()
            stub.send(proto)

    def run(self):
        self._consumer = Consumer(self)
        self._publisher = Publisher(self)

        p = Thread(target=self._publisher.run)
        c = Thread(target=self._consumer.run)

        print(f'Running stub "{repr(self)}" publisher {c.getName()}')
        p.start()
        self._pthread = p

        print(f'Running stub "{repr(self)}" consumer {c.getName()}')
        c.start()
        self._cthread = c

    def join(self):
        p = self._pthread
        c = self._cthread

        print(f'Waiting for stub "{repr(self)}" publisher to finish {p.getName()}')
        p.join()
        print(f'Waiting for stub "{repr(self)}" consumer to finish {c.getName()}')
        c.join()


class Connector:
    _connection = None
    _channel = None

    def __init__(self, _stub):
        self._pipe = _stub._service._pipe
        self._service = _stub._service
        self._stub = _stub
        self._connect()

    def _connect(self):
        conn = self._pipe.active_connection
        credentials = pika.credentials.PlainCredentials(repr(self._service), conn.password)
        print(credentials)
        params = pika.ConnectionParameters(conn.host, conn.port, repr(self._pipe), credentials)
        print(params)

        while True:
            try:
                self._connection = pika.BlockingConnection(parameters=params)
                self._channel = self._connection.channel()
                break
            except Exception as exc:
                print(f'Failed pika connection...\n{exc.args}')
                import time
                time.sleep(RECONNECT_DELAY)


class Publisher(Connector):
    def run(self):
        pass

    def publish(self, proto):
        # check proto type against expected type
        proto_cls = proto.__class__.__name__
        if self._stub._OutStub._in_proto != proto_cls:
            self._stub.raise_wrong_msg_type(proto_cls)

        body = proto.SerializeToString()

        if self._pipe.args.debug:
            print(f'"{self}" stub publishing "{proto_cls}" to {self._stub._out_stub}...')

        self._channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=repr(self._stub._out_stub),
            body=body,
            properties=PROPS
        )

    def publish_callback(self, proto):
        if self._pipe.args.debug:
            print(f'"{self}" stub adding threadsafe publish callback for "{proto.__class__.__name__}"')

        self.publish(proto)
        # cb = functools.partial(self.publish, proto)
        # self._connection.add_callback_threadsafe(cb)


class Consumer(Connector):
    def run(self):
        self.consume()

    def consume(self):

        self._channel.basic_qos(prefetch_count=self._pipe.prefetch)
        queue = repr(self._service) + '.' + repr(self._stub)
        self._channel.basic_consume(queue=queue, on_message_callback=self.consume_callback)
        print(f'Consuming messages on {queue}...')
        self._channel.start_consuming()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self._channel.basic_ack, delivery_tag)
        self._connection.add_callback_threadsafe(cb)

    def consume_callback(self, channel, method, properties, body):
        proto = self._stub._InProto()
        proto.ParseFromString(body)

        if self._pipe.args.debug:
            print(f'"{self}" stub received "{proto.__class__.__name__}" message on {channel}...')

        process_thread = Thread(target=self._stub.process, args=(proto, method))
        process_thread.run()