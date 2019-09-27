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


class AbstractStub:
    def __init__(self, func):
        self.func = func
        raise FileNotFoundError(func.__name__)

    def __call__(self, proto, delivery_tag=None):
        self.func(proto, self.publish_callback)
        if delivery_tag:
            self.ack_callback(delivery_tag)

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

        t = threading.Thread(
            target=self.func,
            args=(proto,),
            kwargs={'delivery_tag': method.delivery_tag}
        )
        t.start()

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self.channel.basic_ack, delivery_tag)
        self.connection.add_callback_threadsafe(cb)


class Service:
    __slots__ = ['stubs', 'messages']
    names = []
    def __init__(self, file, prefetch=1):

        app_path = find_app_path(file)
        sys.path.append(f'{app_path}/.koursaros/')
        self.messages = __import__('messages_pb2')
        service = file.split('/')[-2]

        yamls = json.load(open(app_path + '/.koursaros/yamls.json'))

        class Stubs: pass
        self.stubs = Stubs
        for pipeline, stubs in yamls['pipelines'].items():
            for stub_config in stubs:
                if service == stub_config[1]:
                    self.init_stub(pipeline, stub_config, prefetch)

    def init_stub(self, pipeline, stub_config, prefetch):
        class Stub(AbstractStub): pass

        Stub.pipeline = pipeline
        Stub.pin_in = stub_config[0]
        Stub.service = stub_config[1]
        name = stub_config[2]
        self.names.append(name)
        Stub.name = name
        proto_in = stub_config[3] if stub_config[3] else ''
        proto_out = stub_config[4] if stub_config[4] else ''
        Stub.proto_in = getattr(self.messages, proto_in, None)
        Stub.proto_out = getattr(self.messages, proto_out, None)
        Stub.pin_out = stub_config[5]
        Stub.prefetch = prefetch
        setattr(self.stubs, Stub.name, Stub)
        print(f'Registered {Stub.name}()')

    def main(self, main_func):
        def main_wrap(pipelines, connection_name, **connection):
            main_func(connection_name)
            self.run(pipelines, **connection)

        return main_wrap

    def run(self, pipelines, host='localhost', port=5672, password=None, **kwargs):

        threads = []

        for name in self.names:
            stub = self.stubs.__dict__[name]
            if stub.pipeline in pipelines:
                if getattr(stub, 'func', None) is None:
                    raise ValueError(f'Unassigned stubs: {stub.name}')

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






