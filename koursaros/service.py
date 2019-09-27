import functools
import threading
import time
import sys
import json
import pika
import pika.exceptions
from kctl.utils import find_app_path
from kctl.logger import redirect_out

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent
redirect_out()


class Service:
    __slots__ = ['messages', 'stubs']
    names = []
    def __init__(self, file, prefetch=1):

        app_path = find_app_path(file)
        sys.path.append(f'{app_path}/.koursaros/')
        self.messages = __import__('messages_pb2')
        service = file.split('/')[-2]

        self.stubs = dict()

        yamls = json.load(open(app_path + '/.koursaros/yamls.json'))

        for pipeline, stubs in yamls['pipelines'].items():
            for stub_config in stubs:
                if service == stub_config[1]:
                    name = stub_config[2]
                    configs = dict()
                    configs['prefetch'] = prefetch
                    configs['service'] = service
                    configs['pipeline'] = pipeline
                    configs['pin_in'] = stub_config[0]
                    configs['pin_out'] = stub_config[5]
                    proto_in = stub_config[3] if stub_config[3] else ''
                    proto_out = stub_config[4] if stub_config[4] else ''
                    configs['proto_in'] = getattr(self.messages, proto_in, None)
                    configs['proto_out'] = getattr(self.messages, proto_out, None)
                    host = yamls['connection']['host']
                    port = yamls['connection']['port']
                    password = yamls['connection']['password']
                    credentials = pika.credentials.PlainCredentials(service, password)
                    configs['params'] = pika.ConnectionParameters(host, port, pipeline, credentials)
                    self.stubs[name] = configs

    def stub(self, func):
        return Service.Stub(self, func)

    class Stub:
        def __init__(self, service, func):
            self.func = func
            self.configs = service.stubs[func.__name__]

            while True:
                try:
                    params = self.configs['params']
                    self.connection = pika.BlockingConnection(parameters=params)
                    self.channel = self.connection.channel()
                    break
                except Exception as exc:
                    print(f'Failed pika connection...\n{exc.args}')
                    time.sleep(RECONNECT_DELAY)

            service.stubs[func.__name__] = self

        def __call__(self, proto):
            self.func(proto, self.publish_callback)

        def publish_callback(self, proto):
            cb = functools.partial(self.publish, proto)
            self.connection.add_callback_threadsafe(cb)

        def publish(self, proto):
            body = proto.SerializeToString()
            self.channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=self.configs['pin_out'],
                body=body,
                properties=PROPS
            )

        def consume(self):
            self.channel.basic_qos(prefetch_count=self.configs['prefetch'])
            queue = f'{self.configs["service"]}.{self.func.__name__}'
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=self.consume_callback
            )
            print(f'"{self.func.__name__}" listening on {queue}...')
            self.channel.start_consuming()

        def consume_callback(self, channel, method, properties, body):
            proto = self.configs["proto_in"]()
            proto.ParseFromString(body)

            t = threading.Thread(target=self.func, args=(proto,self.publish_callback))
            t.start()
            self.ack_callback(method.delivery_tag)

        def ack_callback(self, delivery_tag):
            cb = functools.partial(self.channel.basic_ack, delivery_tag)
            self.connection.add_callback_threadsafe(cb)

    def run(self):
        threads = []
        for name, stub in self.stubs.items():
            t = threading.Thread(target=stub.consume)
            print(f'Starting thread {t.getName()}: "{name}"')
            threads.append(t)

        return threads
