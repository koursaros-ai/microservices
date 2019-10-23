import collections
from gnes.flow import *
import argparse
import functools
import pathlib

_Flow = Flow


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def add_wrapper(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        # ignore invalid yaml path
        path = kwargs['yaml_path']
        if not path.isidentifier():
            yaml_path = pathlib.Path(path)
            yaml_path.touch()
            ret = f(*args, **kwargs)
            yaml_path.unlink()
        else:
            ret = f(*args, **kwargs)

        # add custom kwargs
        service = ret._service_nodes[args[1]]
        service['storage'] = kwargs.get('storage', '500Mi')
        service['memory'] = kwargs.get('storage', '500Mi')
        service['cpu'] = kwargs.get('storage', '300m')
        service['replicas'] = kwargs.get('replicas', 1)
        import pdb; pdb.set_trace()
        service['app'] = service['service'].name.lower()
        # service['model'] =
        return ret
    return wrapped


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        self.client_node = kwargs
        return self

    @add_wrapper
    def add_preprocessor(self, *args, **kwargs):
        return super().add_preprocessor(*args, **kwargs)

    @add_wrapper
    def add_encoder(self, *args, **kwargs):
        return super().add_encoder(*args, **kwargs)

    @add_wrapper
    def add_indexer(self, *args, **kwargs):
        return super().add_indexer(*args, **kwargs)

    @add_wrapper
    def add_router(self, *args, **kwargs):
        return super().add_router(*args, **kwargs)

    def to_helm_yaml(self):
        from ruamel.yaml import YAML, StringIO

        _yaml = YAML()

        services = _yaml.load(self.to_swarm_yaml())['services']
        dict_merge(services, self._service_nodes)
        self.helm_yaml = defaultdict(lambda: [])

        for name, service in services.items():
            p_args = vars(configs['parsed_args'])
            yaml_path = p_args.get('yaml_path', None)

            build = False
            if isinstance(yaml_path, str):
                build = True
                model = name
            elif 'yaml_path' in configs['kwargs']:
                model = configs['kwargs']['yaml_path'].lower()
            else:
                model = 'base'

            self.helm_yaml[app] += [dict(
                name=name,
                app=service['app'],
                model=model,
                port_in=p_args.get('port_in', None),
                port_out=p_args.get('port_out', None),
                ctrl_port=p_args.get('ctrl_port', None),
                grpc_port=p_args.get('grpc_port', None),
                command=service.get('command', None).split(),
                replicas=service['replicas'],
                storage=service['storage'],
                memory=service['memory'],
                cpu=service['cpu'],
                image='hub-%s:latest-%s' % (app, model) if build else configs['image']
            )]

        stream = StringIO()
        _yaml.dump(dict(services=dict(self.helm_yaml)), stream)
        return stream.getvalue().strip()

