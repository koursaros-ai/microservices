from inspect import getsource
from grpc_tools import protoc
import yaml as pyyaml
import os
import re

INVALID_PREFIXES = ('_', '.')
IMPORTS = ['from .messages_pb2 import *', 'from koursaros.base import *']

# stub parsing
s = r'\s*'
ns = r'([^\s]*)'
nsp = r'([^\s]+)'
full_regex = rf'{s}{nsp}\({s}{ns}{s}\){s}->{s}{ns}{s}\|{s}{ns}{s}'
FULL_REGEX = re.compile(full_regex)
EXAMPLE = '\nExample: <service>( [variable] ) -> <returns> | <destination>'
STUB_LABELS = ['service', '_rcv_proto', '_send_proto', '_send_stub']


def parse_stub_string(stub_string):
    groups = FULL_REGEX.match(stub_string)

    if not groups:
        raise ValueError(f'\n"{stub_string}" does not'
                         f'match stub string regex {EXAMPLE}')

    groups = groups.groups()
    groups = groups[0].split('.') + list(groups[1:])
    groups = tuple(group if group else None for group in groups)

    return dict(zip(STUB_LABELS, groups))


def get_valid_dirs(path):
    dir_names = [x for x in next(os.walk(path))[1] if not x.startswith(INVALID_PREFIXES)]
    return [path + x for x in dir_names], dir_names


class ClassBottle:
    """Class that formats a python class by being
    given a set of attributes and formatting them
    based on what type of object they are
    """
    @staticmethod
    def check_name(name, obj):
        if name is None:
            raise NameError(f'"None" as name for obj: {obj}')

    class Plain(str):
        """Wrap to indicate that the variable should not
        have quotes around the value
        """

    invalid_names = ['from']
    plain_types = (list, int, Plain, type(None))
    lines = []
    classes = []

    def __init__(self, name, parent_class=None):
        self.name = name
        self.parent = f'({parent_class})' if parent_class else ''

    def digest(self, obj, name=None):
        if name in self.invalid_names:
            raise ValueError(f'Invalid Attribute Name: "{name}"')

        if isinstance(obj, self.plain_types):
            self.check_name(name, obj)
            self.lines.append(f'{name} = {obj}')

        elif isinstance(obj, str):
            self.check_name(name, obj)
            self.lines.append(f'{name} = "{obj}"')

        elif isinstance(obj, dict):
            for key, value in obj.items():
                self.digest(key, value)

        # class or function
        elif callable(obj):
            self.lines += getsource(obj).split('\n')

        # append in order to bottle later
        elif isinstance(obj, self.__class__):
            self.classes.append(obj)

        else:
            raise NotImplementedError(f'var "{name}" of type '
                                      '{type(obj)} not supported')

    def bottle(self, indents=0):
        """recursive function to indent each subclass nested
        within a ClassCompiler.Class
        """
        indent = '    ' * indents
        indented = [indent + line for line in self.lines]
        self.lines += [f'class {self.name}{self.parent}:'] + indented

        indents += 1

        for cls in self.classes:
            cls.bottle(indents=indents)
            self.lines += cls.lines

    def add_headers(self, headers):
        self.lines = headers + self.lines

    def to_string(self):
        self.bottle()
        return '\n'.join(self.lines)


class PipelineBottle(ClassBottle):
    """Subclass of ClassCompiler that compiles Koursaros pipeline

    :param path_manager: Kctl.PathManager object
    """

    def __init__(self, path_manager):

        path_manager.raise_if_no_pipe_root()
        self.path_manager = path_manager
        self.pipe_name = path_manager.pipe_name
        self.pipe_root = path_manager.pipe_root
        self.compile_path = path_manager.compile_path
        self.save_path = self.compile_path + self.pipe_name
        self.name = self.pipe_name
        self.out_file = f'{self.save_path}/__init__.py'
        self.conn_yaml = self.get_yaml(self.pipe_root + '/connections.yaml', 'connections')
        self.stubs_yaml = self.get_yaml(self.pipe_root + '/stubs.yaml', 'stubs')
        self.serv_names, self.serv_yamls = self.get_serv_yamls()


        super().__init__(self.pipe_name, parent_class='Pipeline')


    def cached(self):
        try:
            with open(self.out_file) as f:
                line = f.readline()
                print(line)
                raise SystemExit

        except FileNotFoundError:
            return False

    def get_serv_yamls(self):
        serv_dirs = get_valid_dirs(self.pipe_root + 'services/')
        serv_paths, self.serv_names = serv_dirs
        import pdb; pdb.set_trace()
        yamls = [self.get_yaml(path + '/stubs.yaml', 'stubs') for path in serv_paths]
        return dict(zip(self.serv_names, yamls))

    @staticmethod
    def get_yaml(path, head):
        yaml = pyyaml.safe_load(open(path))
        return yaml[head]

    def compile_connections(self):

        conns = ClassBottle(
            'Connections',
            parent_class='ActivatingContainer'
        )

        conns.digest(self.conn_yaml.keys(), name='__name__')

        for name, configs in self.conn_yaml.items():
            conn = ClassBottle(name, parent_class='Connection')
            conn.digest(configs)
            conns.digest(conn)

        self.digest(conns)

    def compile_stubs(self):

        def wrap(proto):
            return ClassBottle.Plain('messages_pb2.' + proto)

        # keep stubs in list so services can eat them
        stubs = dict()
        for name, string in self.stubs_yaml.items():
            parsed = parse_stub_string(string)
            stub = ClassBottle(name, parent_class='Stub').digest(parsed)

            _RcvProto = stub['_rcv_proto']
            _SendProto = stub['_send_proto']

            stub[_RcvProto] = wrap(_RcvProto)
            stub[_SendProto] = wrap(_SendProto)
            stub['_RcvProto'] = wrap(_RcvProto)
            stub['_SendProto'] = wrap(_RcvProto)

            service = parsed['service']
            stubs[service] = stubs.get(service, []) + stub

        return stubs

    def compile_services(self):

        path = self.pipe_root + 'services/'

        services = ClassBottle('Services', parent_class='ActivatingContainer')
        services.digest(path, name='path')

        all_stubs = self.compile_stubs()
        services.digest(self.serv_names, name='__names__')

        for name in self.serv_names:
            service = ClassBottle(name, parent_class='Service')
            stubs = ClassBottle('Stubs', parent_class='ActivatingContainer')
            yaml = self.serv_yamls[name]
            service.digest(yaml)

            for stub in all_stubs.pop(name):

                stubs.digest(stub)
            services.digest(service)
        self.digest(services)

    def compile_messages(self):
        print(f'Compiling messages for {self.pipe_root}')
        protoc.main((
            '',
            f'-I={self.pipe_root}',
            f'--python_out={self.save_path}',
            f'{self.pipe_root}/messages.proto',
        ))

    def reset_imports(self):
        imports = ''
        all_pipes = next(os.walk(self.save_path))[1]
        for pipe in all_pipes:
            if not pipe.startswith(INVALID_PREFIXES):
                imports += f'from .{pipe} import {pipe}\n'

        with open(f'{self.compile_path}/__init__.py', 'w') as fh:
            fh.write(imports)

    def save(self):
        print(f'Writing to {self.save_path}...')
        os.makedirs(self.save_path, exist_ok=True)
        compiled = self.to_string()
        print(compiled)
        raise SystemExit
        with open(self.out_file, 'w') as fh:
            fh.write(compiled)

        self.reset_imports()
