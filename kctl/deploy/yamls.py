
import yaml
import os
import sys
import pickle

INVALID_PREFIXES = ('_', '.')


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


class App:
    pass


class Pipeline:
    stubs = dict()

    def __init__(self, stubs_path):
        stubs_yaml = yaml.safe_load(open(stubs_path))
        for stub_name, stub_strings in stubs_yaml['stubs'].items():

            if isinstance(stub_strings, str):
                stub_strings = [stub_strings]

            for stub_string in stub_strings:
                stub = Stub(parse_stub_string(stub_string))
                self.stubs[stub_name] = stub


class Service:
    def __init__(self, service_path):
        conn_yaml = yaml.safe_load(open(service_path))
        for key, value in conn_yaml['service'].items():
            setattr(self, key, value)


class Stub:
    def __init__(self, configs):
        messages = __import__('messages_pb2')

        self.service = configs[0]
        if configs[1]:
            self.proto_in = getattr(messages, configs[1], None)
        if configs[2]:
            self.proto_in = getattr(messages, configs[2], None)
        self.stub_out = configs[3]


class Connection:
    def __init__(self, conn_path):
        conn_yaml = yaml.safe_load(open(conn_path))
        for conn_name, configs in conn_yaml['connections'].items():
            setattr(self, conn_name, configs)


def compile_app(app_path):

    sys.path.append(f'{app_path}/.koursaros/')

    conn_path = app_path + '/connections.yaml'
    connection = Connection(conn_path)

    # stubs.yaml
    pipelines = dict()
    pipelines_path = app_path + '/pipelines/'

    for pipeline_name in next(os.walk(pipelines_path))[1]:
        if not pipeline_name.startswith(INVALID_PREFIXES):
            pipeline = Pipeline(pipelines_path + pipeline_name + '/stubs.yaml')
            pipelines[pipeline_name] = pipeline

    # service.yaml
    services = dict()
    services_path = app_path + '/services/'
    for service_name in next(os.walk(services_path))[1]:
        if not service_name.startswith(INVALID_PREFIXES):
            service = Service(services_path + service_name + '/service.yaml')
            services[service_name] = service

    app = App()
    app.path = app_path
    app.connections = connection
    app.pipelines = pipelines
    app.services = services

    with open(app_path + '/.koursaros/app.pickle', 'wb') as fh:
        pickle.dump(app, fh, protocol=pickle.HIGHEST_PROTOCOL)

    with open(app_path + '/.koursaros/app.pickle', 'rb') as fh:
        b = pickle.load(fh)

    print(app == b)
    print(b)
    print(dir(b))


    # with open(app_path + '/.koursaros/yamls.json', 'w') as fh:
    #     fh.write(json.dumps(yamls, indent=4))
    #
    # return app

