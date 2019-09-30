import yaml as pyyaml
import os
import re
from inspect import getsource
from grpc_tools import protoc
from koursaros.utils import find_pipe_path

INVALID_PREFIXES = ('_', '.')


def parse_stub_string(stub_string):
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


class CompiledClass:
    __slots__ = ['lines']

    def __init__(self, name, vars_, parent=None):
        parent = f'({parent})' if parent else ''
        lines = []

        for k, v in vars_.items():

            if isinstance(v, (list, dict, int, self.PlainString)) or v is None:
                lines.append(f'{k} = {v}')

            elif isinstance(v, str):
                lines.append(f'{k} = "{v}"')

            elif callable(v):
                lines += getsource(v).split('\n')

            elif isinstance(v, CompiledClass):
                lines += v.lines

            else:
                raise NotImplementedError(f'var "{k}" of type {type(v)} not implemented')

        self.lines = lines
        self.indent()
        self.lines = [f'class {name}{parent}:'] + self.lines

    def indent(self):
        self.lines = ['    ' + line for line in self.lines] + ['\n']

    def join(self):
        return '\n'.join(self.lines)

    class PlainString(str):
        pass

'''
from koursaros.base import Pipeline

class Piggify(Pipeline):
    class services:
        class pig(Pipeline.Service):
            path = /user/     

            class stubs(Pipeline.Service.Stub):
                channel = 3

    class connections:
        class dev_local(Pipeline.Connection):
            host = 'localhost'
'''


def compile_pipeline(path):
    # sys.path.append(f'{self.path}/.koursaros/')
    # self.messages = __import__('messages_pb2')
    pipeline = dict()
    pipeline['path'] = find_pipe_path(path)
    name = path.split('/')[-2]
    pipeline['name'] = name
    pipeline['connections'] = compile_connections(path)
    pipeline['services'] = compile_services(path)

    pipeline = CompiledClass(name, pipeline, parent='Pipeline')
    return 'import messages_pb2\n\n' + pipeline.join()


# def compile_messages(app_path):
#     messages_path = f'{app_path}/messages'
#
#     print(f'Compiling messages for {app_path}')
#
#     protoc.main((
#         '',
#         f'-I={app_path}',
#         f'--python_out={app_path}/.koursaros',
#         f'{app_path}/messages.proto',
#     ))
#
#     print(f'Compiling yamls for {app_path}')


def compile_connections(path):
    connections = dict()
    path = find_pipe_path(path) + '/connections.yaml'
    connections['path'] = path
    yaml = pyyaml.safe_load(open(path))
    connections['yaml'] = yaml

    for name, configs in yaml['connections'].items():
        connections[name] = compile_connection(name, configs)

    return CompiledClass('connections', connections)


def compile_connection(name, configs):
    connection = dict()
    for key, value in configs.items():
        connection[key] = value

    return CompiledClass(name, connection, parent='Pipeline.Connection')


def compile_services(path):
    services = dict()

    stubs_path = find_pipe_path(path) + '/stubs.yaml'
    stubs_yaml = pyyaml.safe_load(open(stubs_path))
    unserviced_stubs = dict()

    for name, string in stubs_yaml['stubs'].items():
        service, stub = compile_stub(name, string)
        if unserviced_stubs.get(service, None) is None:
            unserviced_stubs[service] = dict()
        unserviced_stubs[service][name] = stub

    path = find_pipe_path(path) + '/services/'
    services['path'] = path

    for name in next(os.walk(path))[1]:
        if not name.startswith(INVALID_PREFIXES):
            stubs = unserviced_stubs.pop(name)
            services[name] = compile_service(path + name, name, stubs)

    return CompiledClass('services', services)


def compile_service(service_path, name, stubs):
    service = dict()

    service['stubs'] = compile_stubs(stubs)

    path = service_path
    yaml = pyyaml.safe_load(open(path + '/service.yaml'))

    for key, value in yaml['service'].items():
        service[key] = value

    return CompiledClass(name, service, parent='Pipeline.Service')


def compile_stubs(stubs):
    return CompiledClass('stubs', stubs, parent='Pipeline.Service')


def compile_stub(name, string):
    service, proto_in, proto_out, stub_out = parse_stub_string(string)

    proto_in = CompiledClass.PlainString('messages_pb2.' + proto_in) if proto_in else None
    proto_out = CompiledClass.PlainString('messages_pb2.' + proto_out) if proto_out else None

    return service, CompiledClass(name, vars(), parent='Pipeline.Service.Stub')
