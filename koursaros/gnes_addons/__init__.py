from gnes.flow import Flow as _Flow
import ruamel
import collections


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

        services = ruamel.yaml.load(self.to_swarm_yaml())['services']
        dict_merge(services, self._service_nodes)

        for service_cls, configs in services.items():
            self.helm_yaml = dict(
                name=service_cls,
                port_in=getattr(configs['parsed_args'], 'port_in', None),
                port_out=getattr(configs['parsed_args'], 'port_out', None),
                ctrl_port=getattr(configs['parsed_args'], 'ctrl_port', None),
                grpc_port=getattr(configs['parsed_args'], 'grpc_port', None),
                command=configs.get('command', None),
                replicas=configs['deploy'].get('replicas', 1) if 'deploy' in configs else 1,
                storage=configs.get('storage', None),
                memory=configs.get('memory', None),
                cpu=configs.get('cpu', None),
                image='gnes-%s:%s' % (configs['service'].name.lower(), service_cls)
            )

        stream = StringIO()
        _yaml.dump(self.helm_yaml, stream)
        return stream.getvalue().strip()
