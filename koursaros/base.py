
import pika
import time
import functools
from threading import Thread
from random import randint
from kctl.cli import get_args

EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class StubError(Exception):
    pass


class Pipeline:

    def __init__(self, file, prefetch=1):
        self.args = get_args()
        self.active_service = file.split('/')[-2]
        self.prefetch = prefetch

        for name in self.services.names:
            service = getattr(self.services, name)
            setattr(self.services, name, service(self))

    class Connection:
        pass

    class Service:
        def __init__(self, pipeline):
            self.pipeline = pipeline

            for name in self.stubs.names:
                stub = getattr(self.stubs, name)
                setattr(stub, 'service', self)
                setattr(stub, 'pipeline', pipeline)

        def run(self):
            threads = []
            for name in self.stubs.names:
                stub = getattr(self.stubs, name)
                t = Thread(target=stub.consume)
                print(f'Starting stub "{stub.name}" ({t.getName()})')
                t.start()
                threads.append((t, stub.name))

            for t, name in threads:
                print(f'Waiting for stub "{name}" to finish ({t.getName()})')
                t.join()

        class Stub:
            def __init__(self, func):
                self.func = func
                setattr(self.service.stubs, self.name, self)

            def __call__(self, proto):
                import pdb;
                pdb.set_trace()
                if self.service.name == self.pipeline.active_service:
                    self.func(proto)
                else:
                    stubs = getattr(self.pipeline.services, self.pipeline.active_service).stubs
                    random_choice = randint(0, len(stubs.names) - 1)
                    stub = getattr(stubs, stubs.names[random_choice])
                    stub.publish_callback(proto, self)

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



