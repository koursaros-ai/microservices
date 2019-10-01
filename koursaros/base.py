
import pika
import time
import functools
from threading import Thread
from random import randint
from kctl.cli import get_args
from inspect import isclass

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class StubError(Exception):
    pass


class IterableAttributesClass:
    """Class that iterates over internal "names" attribute
    and returns respective attribute
    """
    __names__ = []

    def __iter__(self):
        self.iter = iter(self.__names__)
        return self

    def __next__(self):
        name = next(self.iter)
        return getattr(self, name)


class Pipeline:
    """The pipeline object holds services (.services), connection
    parameters (.connections), and command line arguments (.args)

    :param file: __file__ parameter
    :param prefetch: (from pika) Specifies a prefetch window in terms of whole
        messages. This field may be used in combination with the
        prefetch-size field; a message will only be sent in advance
        if both prefetch windows (and those at the channel and connection
        level) allow it. The prefetch-count is ignored by consumers
        who have enabled the no-ack option.
    """
    class Services(IterableAttributesClass):
        def __init__(self, _pipe_ref):
            # hand pipeline reference to each service
            for service in self:
                service(_pipe_ref)

    class Connections(IterableAttributesClass):
        def __init__(self):
            # hand pipeline reference to each service
            for connection in self:
                connection()

    def __init__(self, file, prefetch=1):
        # predicts the active service from file path
        self.active_service = file.split('/')[-2]
        self.args = get_args(self.active_service)
        self.prefetch = prefetch

        # init services with reference to pipeline
        self.Services(self)


class Connection:
    pass


class Service:
    class Stubs(IterableAttributesClass):
        def __init__(self, _pipe_ref, _service_ref):
            for stub in self:
                stub(_pipe_ref, _service_ref)

    def __init__(self, _pipe_ref):
        self._pipe_ref = _pipe_ref
        # hand pipeline and service reference to each stub
        self.Stubs(_pipe_ref, self)

    def run(self):
        for stub in self.Stubs:
            stub_thread = Thread(target=stub.run)


class Stub:
    def __init__(self, item):
        if callable(item):
            self.func = item
            setattr(self.service.stubs, self.name, self)
        else:
            self.func = None
            setattr(self.service.stubs, self.name, self)
            self.__call__(item)

    def __call__(self, proto):
        if self.func is None:
            active = self.pipeline.active_service
            stubs = getattr(self.pipeline.services, active).stubs
            random_choice = randint(0, len(stubs.names) - 1)
            stub = getattr(stubs, stubs.names[random_choice])
            stub.publish_callback(proto, self)
        else:
            self.func(proto)

    def publish(self, proto, stub_out):
        type_in = stub_out.proto_in.__name__
        type_out = proto.__class__.__name__

        if type_in != type_out:
            raise StubError(f'Attemped to send "{type_out}" to "{stub_out.name}"'
                            f'... which expects "{type_in}" message')
        body = proto.SerializeToString()
        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=stub_out.name,
            body=body,
            properties=PROPS
        )

    def publish_callback(self, proto, stub_out):
        print(self.name)
        print(proto)
        cb = functools.partial(self.publish, proto, stub_out)
        self.connection.add_callback_threadsafe(cb)

    def consume(self):

        conn = getattr(self.pipeline.connections, self.pipeline.args.connection)

        credentials = pika.credentials.PlainCredentials(
            self.service.name, conn.password)
        params = pika.ConnectionParameters(
            conn.host, conn.port, self.pipeline.name, credentials)

        while True:
            try:
                self.connection = pika.BlockingConnection(parameters=params)
                self.channel = self.connection.channel()
                break
            except Exception as exc:
                print(f'Failed pika connection...\n{exc.args}')
                time.sleep(RECONNECT_DELAY)

        self.channel.basic_qos(prefetch_count=self.pipeline.prefetch)
        queue = self.service.name + '.' + self.name
        cb = functools.partial(self.consume_callback)
        self.channel.basic_consume(queue=queue, on_message_callback=cb)
        print(f'Listening on {queue}...')
        self.channel.start_consuming()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self.channel.basic_ack, delivery_tag)
        self.connection.add_callback_threadsafe(cb)

    def consume_callback(self, channel, method, properties, body):
        proto = self.proto_in()
        proto.ParseFromString(body)

        t = Thread(target=self.func, args=(proto,))
        t.start()
        self.ack_callback(method.delivery_tag)

    def run(self):
        threads = []
        for name in self.Stubs:
            stub = getattr(self.stubs, name)
            if not isclass(stub):
                t = Thread(target=stub.consume)
                print(f'Starting stub "{stub.name}" ({t.getName()})')
                t.start()
                threads.append((t, stub.name))
            else:
                setattr(self.stubs, name, stub(self.Stub.func))

        for t, name in threads:
            print(f'Waiting for stub "{name}" to finish ({t.getName()})')
            t.join()