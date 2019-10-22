from gnes.flow import Flow as _Flow
import ruamel
import collections
import argparse
from pathlib import Path


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


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        self.client_node = kwargs
        return self

    def to_helm_yaml(self):
        from ruamel.yaml import YAML, StringIO

        _yaml = YAML()

        extra_parser = argparse.ArgumentParser()
        extra_parser.add_argument('--storage', default='500Mi')
        extra_parser.add_argument('--memory', default='500Mi')
        extra_parser.add_argument('--cpu', default='300m')
        service_map =dict()
        services = ruamel.yaml.load(self.to_swarm_yaml(), Loader=ruamel.yaml.Loader)['services']
        dict_merge(services, self._service_nodes)
        helm_yaml = collections.defaultdict(lambda: [])

        for name, configs in services.items():

            yp = configs['parsed_args'].yaml_path
            _type, _subtype = yp.parent.parent.name, yp.parent.name

            p_args = configs['parsed_args']
            extra_args, _ = extra_parser.parse_known_args(configs['unk_args'])

            helm_yaml[_type] += [dict(
                name=name,
                sub_type=_subtype,
                port_in=getattr(p_args, 'port_in', None),
                port_out=getattr(p_args, 'port_out', None),
                ctrl_port=getattr(p_args, 'ctrl_port', None),
                grpc_port=getattr(p_args, 'grpc_port', None),
                command=configs.get('command', None).split(),
                replicas=configs['deploy'].get('replicas', 1) if 'deploy' in configs else 1,
                storage=getattr(extra_args, 'storage', None),
                memory=getattr(extra_args, 'memory', None),
                cpu=getattr(extra_args, 'cpu', None),
                image='hub-%s' % _subtype
            )]

        stream = StringIO()
        self.helm_yaml = dict(services=dict(helm_yaml))
        _yaml.dump(self.helm_yaml, stream)
        return stream.getvalue().strip()
