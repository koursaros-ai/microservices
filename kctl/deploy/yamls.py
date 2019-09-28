
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


class App:
    def __init__(self, app_path):
        self.path = app_path

        sys.path.append(f'{app_path}/.koursaros/')
        self.messages = __import__('messages_pb2')

        # connections.yaml
        self.connections = dict()
        conn_path = app_path + '/connections.yaml'
        self.set_connections(conn_path)

        # stubs.yaml
        self.pipelines = dict()
        pipelines_path = app_path + '/pipelines/'
        self.set_pipelines(pipelines_path)

        # service.yaml
        self.services = dict()
        services_path = app_path + '/services/'
        self.set_services(services_path)

        with open(self.path + '/.koursaros/app.pickle', 'wb') as fh:
            pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)

    def set_connections(self, conn_path):
        conn_yaml = yaml.safe_load(open(conn_path))
        for conn_name, configs in conn_yaml['connections'].items():
            connection = self.Connection(configs)
            self.connections[conn_name] = connection

    def set_pipelines(self, pipelines_path):
        for pipeline_name in next(os.walk(pipelines_path))[1]:
            if not pipeline_name.startswith(INVALID_PREFIXES):
                pipeline_path = pipelines_path + pipeline_name
                self.pipelines[pipeline_name] = self.Pipeline(self.messages, pipeline_path)

    def set_services(self, services_path):
        for service_name in next(os.walk(services_path))[1]:
            if not service_name.startswith(INVALID_PREFIXES):
                service_path = services_path + service_name
                service = self.Service(service_path)
                self.services[service_name] = service

    def configure(self, pipelines, service, connection, prefetch):
        stubs = []
        for pipeline in pipelines:
            for stub in self.pipelines[pipeline].stubs.values():
                if service == stub.service:
                    stub.configure(pipeline, self.connections[connection], prefetch)
                    stubs.append(stub)
        return stubs

    class Connection:
        def __init__(self, dict_):
            for key, value in dict_.items():
                setattr(self, key, value)

    class Service:
        def __init__(self, service_path):
            self.path = service_path
            conn_yaml = yaml.safe_load(open(service_path + '/service.yaml'))
            for key, value in conn_yaml['service'].items():
                setattr(self, key, value)

    class Pipeline:
        def __init__(self, messages, path):
            self.path = path
            self.stubs = dict()

            stubs_yaml = yaml.safe_load(open(path + '/stubs.yaml'))
            for stub_name, stub_string in stubs_yaml['stubs'].items():
                stub = self.Stub(messages, stub_name, stub_string)
                self.stubs[stub_name] = stub

        class Stub:
            def __init__(self, messages, name, stub_string):
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

            def configure(self, pipeline, connection, prefetch):
                self.prefetch = prefetch

                credentials = pika.credentials.PlainCredentials(
                    self.service, connection.password)
                params = pika.ConnectionParameters(
                    connection.host, connection.port, pipeline, credentials)

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


def compile_app(app_path):
    app = App(app_path)
    import pdb;
    pdb.set_trace()
    return app

