import functools
import threading
import time
import sys
import json
import pika
import pika.exceptions
from kctl.utils import find_app_path

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class Service:
    __slots__ = ['_stubs', '_pubbers', '_subbers', 'messages']

    def __init__(self, file, prefetch=1):

        app_path = find_app_path(file)
        sys.path.append(f'{app_path}/.koursaros/')
        module = __import__('messages_pb2')
        self.messages = module

        service = file.split('/')[-2]
        self._stubs = dict()
        self._pubbers = list()
        self._subbers = list()

        yamls = json.load(open(app_path + '/.koursaros/yamls.json'))

        for pipeline, stubs in yamls['pipelines'].items():
            for stub in stubs:
                stub = Stub(self.messages, pipeline, *stub)
                if stub.service == service:
                    stub.prefetch = prefetch
                    self._stubs[stub.func_name] = stub
                    print(f'Registered {stub.func_name}()')

    def pubber(self, pubber_func):
        def pubber_wrap(publish):
            pubber_func(publish)
            return pubber_wrap

        stub = self._stubs.pop(pubber_func.__name__, None)
        raise_name_if_none(stub, pubber_func)
        stub.func = pubber_wrap
        self._pubbers.append(stub)

    def subber(self, subber_func):
        def subber_wrap(proto, publish_callback, ack_callback, delivery_tag):
            subber_func(proto, publish_callback)
            ack_callback(delivery_tag)
            return subber_wrap

        stub = self._stubs.pop(subber_func.__name__, None)
        raise_name_if_none(stub, subber_func)
        stub.func = subber_wrap
        self._subbers.append(stub)

    def main(self, main_func):
        def main_wrap(pipelines, connection_name, **connection):
            main_func(connection_name)
            self.run(pipelines, **connection)

        return main_wrap

    def run(self, pipelines, host='localhost', port=5672, password=None, **kwargs):

        for stub in self._stubs:
            if stub.pipeline in pipelines:
                raise ValueError(f'Unassigned stubs: {stub.func_name}()')

        threads = []

        # pubbers
        for stub in self._pubbers:
            if stub.pipeline in pipelines:
                stub.host = host
                stub.port = port
                stub.password = password
                stub.rabbitmq_connect()
                t = threading.Thread(target=stub.func, args=(stub.publish,))
                print(f'Starting thread {t.getName()}')
                t.start()
                threads.append((t, stub))

        # subbers
        for stub in self._subbers:
            if stub.pipeline in pipelines:
                stub.host = host
                stub.port = port
                stub.password = password
                stub.rabbitmq_connect()
                t = threading.Thread(target=stub.consume)
                print(f'Starting thread {t.getName()}: {stub.func_name}()...')
                t.start()
                threads.append((t, stub))

        for t, stub in threads:
            print(f'Joining thread {t.getName()}: {stub.func_name}()...')
            t.join()


class Stub:
    __slots__ = ['service', 'proto_in', 'proto_out', 'func_name', 'func', 'prefetch',
                 'connection', 'channel', 'pin_out', 'host', 'password', 'pipeline', 'port']

    def __init__(self, messages, pipeline, pin_in, service, func_name, proto_in, proto_out, pin_out):
        self.pipeline = pipeline
        self.service = service
        self.pin_out = pin_out
        self.func_name = func_name
        self.proto_in = get_module_attr(messages, proto_in)
        self.proto_out = get_module_attr(messages, proto_out)

        # runtime attributes
        self.func = None
        self.host = None
        self.port = None
        self.password = None
        self.prefetch = None
        self.connection = None
        self.channel = None

    def rabbitmq_connect(self):
        while True:
            try:
                credentials = pika.credentials.PlainCredentials(
                    self.service,
                    self.password
                )
                params = pika.ConnectionParameters(
                    self.host,
                    self.port,
                    self.pipeline,
                    credentials
                )
                self.connection = pika.BlockingConnection(parameters=params)
                self.channel = self.connection.channel()
                break
            except Exception as exc:
                print(f'Failed pika connection on: {self.host}:{self.port}\n{exc.args}')
                time.sleep(RECONNECT_DELAY)

    def publish_callback(self, proto):
        cb = functools.partial(self.publish, proto)
        self.connection.add_callback_threadsafe(cb)

    def publish(self, proto):
        body = proto.SerializeToString()
        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=self.pin_out,
            body=body,
            properties=PROPS
        )

    def consume(self):
        self.channel.basic_qos(prefetch_count=self.prefetch)
        self.channel.basic_consume(
            queue=f'{self.service}.{self.func_name}',
            on_message_callback=self.consume_callback
        )
        self.channel.start_consuming()

    def consume_callback(self, channel, method, properties, body):
        proto = self.proto_in()
        proto.ParseFromString(body)
        args = (proto, self.publish_callback, self.ack_callback, method.delivery_tag)
        t = threading.Thread(target=self.func, args=args)
        t.start()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self.channel.basic_ack, delivery_tag)
        self.connection.add_callback_threadsafe(cb)


def raise_name_if_none(var, obj):
    if not var:
        raise ValueError(f'"{obj.__name__}" not found in stubs.yaml')


def get_module_attr(module, attr):
    if attr:
        return getattr(module, attr, None)
    else:
        return None
