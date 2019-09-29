
import yaml
import os
import sys
import pickle
import pika
import time
import functools
from threading import Thread

INVALID_PREFIXES = ('_', '.')
EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class PipelineException(Exception):
    pass


class Pipeline:

    @staticmethod
    def construct(pipe_path):
        Pipeline.path = pipe_path
        Pipeline.name = pipe_path.split('/')[-2]

        # connections
        conn_path = pipe_path + '/connections.yaml'
        Pipeline.set_connections(conn_path)

        # stubs
        stubs_path = pipe_path + '/stubs.yaml'
        sys.path.append(f'{pipe_path}/.koursaros/')
        messages = __import__('messages_pb2')
        Pipeline.set_stubs(stubs_path, messages)

        # services
        Pipeline.services = dict()
        services_path = pipe_path + '/services/'
        Pipeline.set_services(services_path)

        Pipeline.check_unallocated()

    @staticmethod
    def set_connections(conn_path):
        Pipeline.connections = dict()
        conn_yaml = yaml.safe_load(open(conn_path))
        for conn_name, configs in conn_yaml['connections'].items():
            connection = Pipeline.Connection(conn_path, configs)
            Pipeline.connections[conn_name] = connection

    @staticmethod
    def set_stubs(stubs_path, messages):
        Pipeline.stubs = dict()
        stubs_yaml = yaml.safe_load(open(stubs_path))
        for stub_name, stub_string in stubs_yaml['stubs'].items():
            stub = Pipeline.Stub(stubs_path, stub_name, stub_string, messages)
            Pipeline.stubs[stub_name] = stub

    @staticmethod
    def set_services(services_path):
        Pipeline.services = dict()
        service_names = next(os.walk(services_path))[1]
        for service_name in service_names:
            if not service_name.startswith(INVALID_PREFIXES):
                service_path = services_path + service_name
                service_yaml = yaml.safe_load(open(service_path + '/service.yaml'))

                class Service:
                    class Messages:
                        def register_proto(self, proto):
                            if proto is not None:
                                setattr(self, proto.__name__, proto)

                    def stub(self, name):
                        def decorator(func):
                            self.stubs[name] = func
                            return func

                        return decorator

                    name = service_name
                    path = service_path
                    messages = Messages()
                    stubs = dict()

                    for key, value in service_yaml['service'].items():
                        vars()[key] = value

                    for stub_name in list(Pipeline.stubs):
                        if name == Pipeline.stubs[stub_name].service:
                            stub = Pipeline.stubs.pop(stub_name)
                            stubs[stub_name] = stub

                            messages.register_proto(stub.proto_in)
                            messages.register_proto(stub.proto_out)

                Pipeline.services[service_name] = Service

    @staticmethod
    def check_unallocated():
        unallocated = [f'{stub.service}.{stub.name}' for stub in Pipeline.stubs.values()]
        if unallocated:
            raise PipelineException(f'Unallocated stubs: {unallocated}')

    class Connection:
        def __init__(self, conn_path, configs):
            self.path = conn_path
            for key, value in configs.items():
                setattr(self, key, value)

    class Stub:
        def __init__(self, path, name, stub_string, messages):
            self.path = path
            self.name = name
            self.stub_string = stub_string
            self.parse_stub_string(stub_string)

            parsed = self.parse_stub_string(stub_string)

            self.service = parsed[0]
            if parsed[1]:
                self.proto_in = getattr(messages, parsed[1], None)
            else:
                self.proto_in = None
            if parsed[2]:
                self.proto_out = getattr(messages, parsed[2], None)
            else:
                self.proto_out = None

            self.stub_out = parsed[3]

        def __call__(self, proto):
            self.func(proto, self.publish_callback)

        @staticmethod
        def parse_stub_string(stub_string):
            import re
            s = r'\s*'
            ns = r'([^\s]*)'
            nsp = r'([^\s]+)'
            full_regex = rf'{s}{nsp}\({s}{ns}{s}\){s}->{s}{ns}{s}\|{s}{ns}{s}'
            full_regex = re.compile(full_regex)
            example = '\nExample: <service>( [variable] ) -> <returns> | <destination>'
            groups = full_regex.match(stub_string)

            if not groups:
                raise ValueError(f'\n"{stub_string}" does not match stub string regex{example}')

            groups = groups.groups()
            groups = groups[0].split('.') + list(groups[1:])
            groups = tuple(group if group else None for group in groups)

            return groups

        def configure(self, conn_name, prefetch):
            self.prefetch = prefetch
            connection = Pipeline.connections[conn_name]

            credentials = pika.credentials.PlainCredentials(
                self.service, connection.password)
            params = pika.ConnectionParameters(
                connection.host, connection.port, Pipeline.name, credentials)

            while True:
                try:
                    self.connection = pika.BlockingConnection(parameters=params)
                    self.channel = self.connection.channel()
                    break
                except Exception as exc:
                    print(f'Failed pika connection...\n{exc.args}')
                    time.sleep(RECONNECT_DELAY)

        def publish_callback(self, proto):
            cb = functools.partial(self.publish, proto)
            self.connection.add_callback_threadsafe(cb)

        def publish(self, proto):
            body = proto.SerializeToString()
            self.channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=self.stub_out,
                body=body,
                properties=PROPS
            )

        def consume(self):
            self.channel.basic_qos(prefetch_count=self.prefetch)
            queue = self.service + '.' + self.name
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=self.consume_callback
            )
            print(f'Listening on {queue}...')
            self.channel.start_consuming()

        def consume_callback(self, channel, method, properties, body):
            proto = self.proto_in()
            proto.ParseFromString(body)

            t = Thread(target=self.func, args=(proto, self.publish_callback))
            t.start()
            self.ack_callback(method.delivery_tag)

        def ack_callback(self, delivery_tag):
            cb = functools.partial(self.channel.basic_ack, delivery_tag)
            self.connection.add_callback_threadsafe(cb)


def compile_app(pipe_path):
    Pipeline.construct(pipe_path)
    # with open(pipe_path + '/.koursaros/app.pickle', 'wb') as fh:
    #     pickle.dump(Pipeline, fh, protocol=pickle.HIGHEST_PROTOCOL)

    import pdb;
    pdb.set_trace()

    return Pipeline

