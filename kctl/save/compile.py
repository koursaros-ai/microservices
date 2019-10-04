
from .bottler import ClassBottler

from grpc_tools import protoc
import yaml as pyyaml
import os
import re
from collections import OrderedDict


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


class PipelineBottler(ClassBottler):
    """Subclass of ClassCompiler that compiles Koursaros pipeline

    :param path_manager: Kctl.PathManager object
    """

    def __init__(self, path_manager):

        path_manager.raise_if_no_pipe_root()
        pm = path_manager

        self.conn_yaml = self.get_yamls([pm.conn_path], 'connections')[0]
        self.stubs_yaml = self.get_yamls([pm.stubs_path], 'stubs')[0]
        serv_paths = OrderedDict(pm.serv_paths)
        self.serv_yamls = self.get_yamls(serv_paths.values(), 'service')
        self.serv_names = serv_paths.keys()

        self.hashed_yamls = '#' + pm.conn_hash + pm.stubs_hash + ''.join(pm.serv_hashes) + '\n'
        self.pm = pm

        super().__init__(pm.pipe_name, parent_class='Pipeline')

    @staticmethod
    def get_yamls(paths, head):
        return [pyyaml.safe_load(open(path))[head] for path in paths]

    def cached(self):
        try:
            with open(self.pm.pipe_save_file) as f:
                firstline = f.readline()
                return True if firstline == self.hashed_yamls else False

        except FileNotFoundError:
            return False

    def compile_connections(self):

        conns = ClassBottler(
            'Connections',
            parent_class='ActivatingContainer'
        )

        conns.digest(list(self.conn_yaml.keys()), name='__names__')

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

        services = ClassBottler('Services', parent_class='ActivatingContainer')
        all_stubs = self.compile_stubs()
        services.digest(list(self.serv_names), name='__names__')

        for name, yaml in zip(self.serv_names, self.serv_yamls):
            service = ClassBottler(name, parent_class='Service')
            stubs = ClassBottler('Stubs', parent_class='ActivatingContainer')
            service.digest(yaml)

            for stub in all_stubs.pop(name):

                stubs.digest(stub)
            services.digest(service)

        self.digest(services)

    def compile_messages(self):
        print(f'Compiling messages for {self.pm.pipe_root}')
        protoc.main((
            '',
            f'-I={self.pm.pipe_root}',
            f'--python_out={self.pm.pipe_save_dir}',
            f'{self.pm.pipe_root}/messages.proto',
        ))

    def save(self):
        print(f'Writing to {self.pm.pipe_save_dir}...')
        os.makedirs(self.pm.pipe_save_dir, exist_ok=True)
        compiled = self.to_string()
        with open(self.pm.pipe_save_file, 'w') as fh:
            fh.write(self.hashed_yamls + compiled)
