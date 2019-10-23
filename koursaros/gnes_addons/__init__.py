from gnes.flow import *
import pathlib
import functools

_Flow = Flow


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        self.client_node = kwargs
        return self

    def add(self, service: Union['Service', str], name: str = None, *args, **kwargs):
        import pdb;
        pdb.set_trace()
        app = service.name.lower()
        model = kwargs.get('name', 'base')
        image = 'gnes/gnes:latest-alpine'
        supercall = functools.partial(super().add, service, name, *args, **kwargs)
        if model == 'base':
            ret = supercall()
        else:
            yaml_path = kwargs['yaml_path']

            if yaml_path.isidentifier():
                ret = supercall()
                model = yaml_path.lower()
            else:
                # ignore invalid yaml path
                path = pathlib.Path(yaml_path)
                path.touch()
                ret = supercall()
                path.unlink()
                model = yaml_path
                image = 'hub-%s:latest-%s' % (app, model)

        # add custom kwargs
        try:
            name = '%s%d' % (service, self._service_name_counter[service]-1) if not name else name

            v = ret._service_nodes[name]
            v['storage'] = kwargs.get('storage', '500Mi')
            v['memory'] = kwargs.get('storage', '500Mi')
            v['cpu'] = kwargs.get('storage', '300m')
            v['replicas'] = kwargs.get('replicas', 1)
            v['app'] = app
            v['model'] = model
            v['image'] = image
        except Exception as e:
            print(e)
            import pdb; pdb.set_trace()
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

