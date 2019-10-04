
from .bottler import ClassBottler
from operator import itemgetter
from grpc_tools import protoc
from hashlib import md5
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


class PipelineBottler(ClassBottler):
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
        self.serv_paths, self.serv_yamls = self.get_serv_yamls()

        super().__init__(self.pipe_name, parent_class='Pipeline')

    @staticmethod
    def md5_dict(dict_):
        """Sorts a dict by keys and returns a concat md5 hash of the key and values"""
        tuples = sorted(dict_.items(), key=itemgetter(0))
        hashed_list = [key + md5(value).hexdigest() for key, value in tuples]
        return ''.join(hashed_list)

    @staticmethod
    def open_dict(dict_):
        """open a dictionary of filepaths to bytes (paths are the values)"""
        return {key: open(path, 'rb').read() for key, path in dict_.items()}

    def cached(self):
        try:
            print(self.out_file)
            with open(self.out_file) as f:
                firstline = f.readline()
                plaintext = self.open_dict(self.serv_paths)
                hashed = self.md5_dict(plaintext)
                return True if firstline == hashed else False

        except FileNotFoundError:
            return False

    def get_serv_yamls(self):
        serv_dirs = get_valid_dirs(self.pipe_root + 'services/')
        serv_paths, serv_names = serv_dirs
        serv_paths = [path + '/service.yaml' for path in serv_paths]

        yamls = [self.get_yaml(path, 'service') for path in serv_paths]
        return dict(zip(serv_names, serv_paths)), dict(zip(serv_names, yamls))

    @staticmethod
    def get_yaml(path, head):
        yaml = pyyaml.safe_load(open(path))
        return yaml[head]

    def compile_connections(self):

        conns = ClassBottler(
            'Connections',
            parent_class='ActivatingContainer'
        )

        conns.digest(list(self.conn_yaml.keys()), name='__name__')

        for name, configs in self.conn_yaml.items():
            conn = ClassBottler(name, parent_class='Connection')
            conn.digest(configs)
            conns.digest(conn)

        self.digest(conns)

    def compile_stubs(self):

        def wrap(proto):
            return ClassBottler.Plain('messages_pb2.' + proto)

        # keep stubs in list so services can eat them
        stubs = dict()
        for name, string in self.stubs_yaml.items():
            stub = dict()

            parsed = parse_stub_string(string)

            _RcvProto = parsed['_rcv_proto']
            _SendProto = parsed['_send_proto']

            if _RcvProto is not None:
                stub[_RcvProto] = wrap(_RcvProto)

            if _SendProto is not None:
                stub[_SendProto] = wrap(_SendProto)

            stub['_RcvProto'] = wrap(_RcvProto)
            stub['_SendProto'] = wrap(_RcvProto)

            service = parsed['service']

            stubb = ClassBottler(name, parent_class='Stub')
            stubb.digest(stub)
            stubs[service] = stubs.get(service, []) + [stubb]

        return stubs

    def compile_services(self):

        path = self.pipe_root + 'services/'

        services = ClassBottler('Services', parent_class='ActivatingContainer')
        services.digest(path, name='path')

        all_stubs = self.compile_stubs()
        services.digest(self.serv_names, name='__names__')

        for name in self.serv_names:
            service = ClassBottler(name, parent_class='Service')
            stubs = ClassBottler('Stubs', parent_class='ActivatingContainer')
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
