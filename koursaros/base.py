
import pika
import time
import functools
from threading import Thread

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class Stub:
    def __init__(self, func):
        self.func = func

    def func(self, proto):
        raise NotImplementedError('Stub function not implemented...')

    def __call__(self, proto):
        if self.service == self.:
        self.func(proto, self.publish_callback)

    def consume(self, conn, prefetch=1):

        credentials = pika.credentials.PlainCredentials(
            self.service, conn.password)
        params = pika.ConnectionParameters(
            conn.host, conn.port, self.service.pipeline.name, credentials)

        while True:
            try:
                self.connection = pika.BlockingConnection(parameters=params)
                self.channel = self.connection.channel()
                break
            except Exception as exc:
                print(f'Failed pika connection...\n{exc.args}')
                time.sleep(RECONNECT_DELAY)

        self.channel.basic_qos(prefetch_count=prefetch)
        queue = self.service.name + '.' + self.name
        self.channel.basic_consume(
            queue=queue,
            on_message_callback=self.consume_callback
        )
        print(f'Listening on {queue}...')
        self.channel.start_consuming()

    def publish(self, proto):
        body = proto.SerializeToString()
        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=self.stub_out,
            body=body,
            properties=PROPS
        )

    def publish_callback(self, proto):
        cb = functools.partial(self.publish, proto)
        self.connection.add_callback_threadsafe(cb)

    def ack_callback(self, delivery_tag):
        cb = functools.partial(self.channel.basic_ack, delivery_tag)
        self.connection.add_callback_threadsafe(cb)

    def consume_callback(self, channel, method, properties, body):
        proto = self.proto_in()
        proto.ParseFromString(body)

        t = Thread(target=self.func, args=(proto,))
        t.start()
        self.ack_callback(method.delivery_tag)



class Pipeline:

    def __init__(self, path):

        if self.unserviced_stubs.names:
            raise BrokenPipeError(f'Unserviced stubs: {self.unserviced_stubs.names}')

    class Connection:
        def __init__(self, configs):
            for key, value in configs.items():
                setattr(self, key, value)

    class Service:
        def __init__(self, pipeline, path, name):

        def stubs(self, name):
            def decorator(func):
                setattr(self.stubs)
                self.stubs[name] = func
                return func

            return decorator

        def configure(self, conn_name, prefetch):
            for stub in self.stubs:
            self.prefetch = prefetch
            connection = Pipeline.connections[conn_name]

        def run(self):
            threads = []
            for stub in self.stubs.values():
                t = Thread(target=stub.consume)
                print(f'Starting stub "{stub.name}" ({t.getName()})')
                t.start()
                threads.append((t, stub.name))

            for t, name in threads:
                print(f'Waiting for stub "{name}" to finish ({t.getName()})')
                t.join()