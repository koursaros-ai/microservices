from gnes.flow import *
import pathlib

_Flow = Flow


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        self.client_node = kwargs
        return self

    def add(self, *args, **kwargs):
        # ignore invalid yaml path
        f = super().add(*args, **kwargs)
        yaml_path = kwargs.get('yaml_path', None)
        build = False

        if yaml_path is None:
            ret = f(*args, **kwargs)
            model = 'base'

        elif yaml_path.isidentifier():
            ret = f(*args, **kwargs)
            model = yaml_path.lower()
        else:
            path = pathlib.Path(yaml_path)
            path.touch()
            ret = f(*args, **kwargs)
            path.unlink()
            model = yaml_path
            build = True

        # add custom kwargs
        v = ret._service_nodes[kwargs['name']]
        v['storage'] = kwargs.get('storage', '500Mi')
        v['memory'] = kwargs.get('storage', '500Mi')
        v['cpu'] = kwargs.get('storage', '300m')
        v['replicas'] = kwargs.get('replicas', 1)
        v['app'] = v['service'].name.lower()
        v['model'] = model
        v['image'] = kwargs.get(
            'image', 'hub-%s:latest-%s' % (v['app'], v['model']) if build else 'gnes/gnes:latest-alpine'
        )
        return ret

    def to_helm_yaml(self):
        from ruamel.yaml import YAML, StringIO
        _yaml = YAML()

        self.helm_yaml = defaultdict(lambda: [])

        for k, v in self._service_nodes.items():
            defaults_kwargs, _ = service_map[
                v['service']]['parser']().parse_known_args(['--yaml_path', 'TrainableBase'])

            non_default_kwargs = {
                k: v for k, v in vars(v['parsed_args']).items() if getattr(defaults_kwargs, k) != v}

            command = '%s %s' % (
                service_map[v['service']]['cmd'],
                ' '.join(['--%s %s' % (k, v) for k, v in non_default_kwargs.items()])
            )

            self.helm_yaml[v['app']] += [dict(
                name=k,
                app=v['app'],
                model=v['model'],
                port_in=v['parsed_args'].get('port_in', None),
                port_out=v['parsed_args'].get('port_out', None),
                ctrl_port=v['parsed_args'].get('ctrl_port', None),
                grpc_port=v['parsed_args'].get('grpc_port', None),
                command=command.split(),
                replicas=v['replicas'],
                storage=v['storage'],
                memory=v['memory'],
                cpu=v['cpu'],
                image=v['image']
            )]

        stream = StringIO()
        _yaml.dump(dict(services=dict(self.helm_yaml)), stream)
        return stream.getvalue().strip()

