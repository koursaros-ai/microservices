import yaml as pyyaml
import os
from inspect import getsource
from grpc_tools import protoc
from koursaros.utils import find_pipe_path

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


class CompiledClass:
    __slots__ = ['lines']

    def __init__(self, name, vars_, parent=None):
        parent = f'({parent})' if parent else ''
        lines = []

        for k, v in vars_.items():

            if isinstance(v, str):
                lines.append(f'{k} = "{v}"')

            elif isinstance(v, (list, dict, int)) or v is None:
                lines.append(f'{k} = {v}')

            elif callable(v):
                lines += getsource(v).split('\n')

            elif isinstance(v, CompiledClass):
                v.indent()
                lines += v.lines

            else:
                raise NotImplementedError(f'var "{k}" of type {type(v)} not implemented')

        self.lines = [f'class {name}{parent}:'] + lines
        self.indent()

    def indent(self):
        self.lines = ['    ' + line for line in self.lines]

    def join(self):
        return '\n'.join(self.lines)

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
    path = find_pipe_path(path)
    name = path.split('/')[-2]
    connections = compile_connections(path)
    services = compile_services(path, name)

    pipeline = CompiledClass(name, vars(), parent='Pipeline')
    return pipeline.join()


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
    path = find_pipe_path(path) + '/connections.yaml'
    yaml = pyyaml.safe_load(open(path))

    for name, configs in yaml['connections'].items():
        vars()[name] = compile_connection(name, configs)

    return CompiledClass('connections', vars())


def compile_connection(name, configs):
    for key, value in configs.items():
        vars()[key] = value

    return CompiledClass(name, vars(), parent='Pipeline.Connection')


def compile_services(path, pipeline):
    stubs_path = find_pipe_path(path) + '/stubs.yaml'
    stubs_yaml = pyyaml.safe_load(open(stubs_path))
    unserviced_stubs = dict()

    for name, string in stubs_yaml['stubs'].items():
        unserviced_stubs[name] = compile_stub(name, string, pipeline)

    path = find_pipe_path(path) + '/services/'
    for name in next(os.walk(path))[1]:
        if not name.startswith(INVALID_PREFIXES):
            vars()[name] = compile_service(path + name, name)

    return CompiledClass('services', vars())


def compile_service(service_path, name):
    path = service_path
    yaml = pyyaml.safe_load(open(path + 'service.yaml'))

    for key, value in yaml['service'].items():
        vars()[key] = value

    return CompiledClass(name, vars(), parent='Pipeline.Service')


def compile_stub(name, string, pipeline):
    service, proto_in, proto_out, stub_out = parse_stub_string(string)

    proto_in = 'messages_pb2.' + proto_in if proto_in else None
    proto_out = 'messages_pb2.' + proto_out if proto_out else None

    return CompiledClass(name, vars(), parent='Pipeline.Service.Stub')
