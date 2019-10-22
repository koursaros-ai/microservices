from collections import Mapping
from pathlib import Path
from gnes.flow import *
import argparse

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
                and isinstance(merge_dct[k], Mapping)):
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

        services = _yaml.load(self.to_swarm_yaml())['services']
        dict_merge(services, self._service_nodes)
        self.helm_yaml = dict(services=defaultdict(lambda: []))

        for name, configs in services.items():
            p_args = vars(configs['parsed_args'])
            extra_args = vars(extra_parser.parse_known_args(configs['unk_args'])[0])
            yaml_path = p_args.get('yaml_path', None)
            app = configs['service'].name.lower()

            if isinstance(yaml_path, str):
                model = Path(yaml_path).parent.name
            else:
                import pdb; pdb.set_trace()
                model = configs['kwargs']['yaml_path'].lower()

            self.helm_yaml['services'][app] += [dict(
                name=name,
                app=app,
                model=model,
                port_in=p_args.get('port_in', None),
                port_out=p_args.get('port_out', None),
                ctrl_port=p_args.get('ctrl_port', None),
                grpc_port=p_args.get('grpc_port', None),
                command=configs.get('command', None).split(),
                replicas=configs['deploy'].get('replicas', 1) if 'deploy' in configs else 1,
                storage=extra_args.get('storage', None),
                memory=extra_args.get('memory', None),
                cpu=extra_args.get('cpu', None),
                image='hub-%s:latest-%s' % (app, model)
            )]

        stream = StringIO()
        _yaml.dump(self.helm_yaml, stream)
        return stream.getvalue().strip()

