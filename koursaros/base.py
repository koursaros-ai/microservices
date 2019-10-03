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


def cls(obj):
    return obj.__class__.__name__


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
        print(self.__activerefs__)
        for clas in list(self):
            cls_name = clas.__name__
            __active__ = True if cls_name in active_names else False
            print(clas, cls_name, __active__)
            setattr(clas, '__active__', __active__)

            instance = clas(*args, **kwargs)
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

    def getactive(self):
        """getactive() assumes that their is one __active__
        subclass... will raise if there is not exactly one
        """
        if len(self.__activerefs__) != 1:
            raise self.NotOneActiveError('Not exactly one __active__ subclass: '
                                         f'{self.__activerefs__}')

        return self.__activerefs__[0]

    def randomactive(self):
        rand_int = randint(0, len(self.__activerefs__) - 1)

        return self.__activerefs__[rand_int]

    class NotOneActiveError(Exception):
        pass


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

        # get command line arguments
        self.args = get_args()
        self.debug = self.args.debug
        self.prefetch = prefetch

        self.Connections = self.Connections([self.args.connection])

        if package is None:
            active_service_name = None
            self.active_service = None
        else:
            active_service_name = package.split('.')[-1]
            KctlLogger.init()

        if self.debug:
            print(f'Initializing {self}.Services')

        # init services with reference to pipeline
        self.Services = self.Services([active_service_name], self)

        # set stub with refs to each other
        # for service in self.Services:
        #     for stub in service.Stubs:
        #         stub.bind_send_stub()


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
        self._pipe = _pipe
        self._debug = _pipe.debug

        if self._debug:
            print(f'Initializing "{self}" service...')

        active_stub_names = self.Stubs.__names__ if self.__active__ else []

        # init stubs with reference to pipeline and service
        self.Stubs = self.Stubs(active_stub_names, self)

    def run(self):
        for stub in self.Stubs:
            stub.run()
        for stub in self.Stubs:
            stub.join()

    # def bind_send_stub(self):
    #     if self.send_stub is not None:
    #
    #         for service in self._pipe.Services:
    #             for stub in service.Stubs:
    #                 if repr(stub) == self.send_stub:
    #                     self.OutStub = stub
    #
    #         self._should_send = True
    #
    #         if self.RcvStub is None:
    #             self.raise_stub_not_found()
    #
    #         if self.send_proto != self.OutStub.InProto:
    #             self.raise_wrong_msg_type(self.send_proto)


class Stub(ReprClassName):
    __active__ = False

    _rcv_proto = None
    _send_proto = None
    _RcvProto = None
    _SendProto = None

    _send_stub = None

    _should_send = False

    _consumer = None
    _publisher = None

    _pthread = None
    _cthread = None

    def __init__(self, _service):
        self._service = _service
        self._pipe = _service._pipe
        self._debug = self._pipe.debug

        if self._debug:
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
               f'but expected "{cls(self._SendProto)}" message')
        raise self.WrongMessageTypeError(msg)

    def raise_stub_not_found(self):
        msg = f'{repr(self)} could not find "{self._send_stub}" stub to send to'
        raise self.StubNotFoundError(msg)

    def raise_not_active(self):
        # if the parent service is not active then crash
        msg = (f'Cannot use stubs from "{self._service}"'
               f'service in "{self._pipe.Services.getactive()}" service')
        raise self.NotInActiveServiceError(msg)

    def raise_no_return(self):
        msg = (f'"{self}" stub did not return anything,'
               f'but it should be sending to "{self._send_stub}" stub')
        raise self.NoReturnError(msg)

    def raise_should_not_return(self):
        msg = f'"{self}" stub should not return anything...'
        raise self.ShouldNotReturnError(msg)

    def process(self, proto, method=None):

        if self._debug:
            print(f'"{self}" stub processing "{cls(proto)}"...')

        returned = self.func(proto)

        if self._debug:
            print(f'"{self.func.__name__}" returned "{cls(returned)}"...')

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
            if self._debug:
                print(f'"{self}" stub sending ack callback: {tag}')

            self._consumer.ack_callback(tag)

    def send(self, proto):

        if self._pipe.debug:
            not_ = '' if self.__active__ else 'not '
            print(f'"{self}" is {not_}active...')

        if self.__active__:
            self._publisher.publish(proto)
        else:
            # get active service then send from random active stub
            self._pipe.Services.getactive().Stubs.randomactive().send(proto)

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


class Connector(ReprClassName):
    _connection = None
    _channel = None
    _debug = False

    def __init__(self, _stub):
        self._pipe = _stub._service._pipe
        self._debug = self._pipe.debug
        self._service = _stub._service
        self._stub = _stub
        self._connect()

    def _connect(self):
        conn = self._pipe.Connections.getactive()
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

    def check_send_proto(self, proto):
        """Checks an outgoing proto against the
        type that the receiving stub expects
        """
        if cls(self._stub.RcvStub.InProto) != cls(proto):
            self._stub.raise_wrong_msg_type(cls(proto))

    def publish(self, proto):
        # tag outgoing protos with their class names
        proto.cls = proto.__class__.__name__

        self.check_send_proto(proto)

        body = proto.SerializeToString()

        send_queue = repr(self._stub._SendStub)

        if self._debug:
            print(f'"{self._stub}" stub publishing "{cls(proto)}" to {send_queue}...')

        self._channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=send_queue,
            body=body,
            properties=PROPS
        )

        if self._debug:
            print(f'"{self._stub}" stub published "{cls(proto)}"')


class Consumer(Connector):
    def run(self):
        self.consume()

    def consume(self):

        self._channel.basic_qos(prefetch_count=self._pipe.prefetch)
        queue = self._stub.queue
        self._channel.basic_consume(queue=queue, on_message_callback=self.consume_callback)
        print(f'Consuming messages on {queue}...')
        self._channel.start_consuming()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self._channel.basic_ack, delivery_tag)
        self._connection.add_callback_threadsafe(cb)

    def consume_callback(self, channel, method, properties, body):
        proto = self._stub.InProto()
        proto.ParseFromString(body)

        if self._pipe.args.debug:
            print(f'"{self}" stub received "{proto.__class__.__name__}" message on {channel}...')

        process_thread = Thread(target=self._stub.process, args=(proto, method))
        process_thread.run()