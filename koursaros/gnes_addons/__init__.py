from gnes.flow import *
import pathlib
import functools

_Service = Service
_Flow = Flow


class Service(_Service):
    Client = 5


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        return self.add(Service.Client, **kwargs)

    def add(self, service: Union['Service', str], name: str = None, *args, **kwargs):
        supercall = functools.partial(super().add, service, name, *args, **kwargs)
        app = service.name.lower()
        model = name if name else 'base'
        yaml_path = kwargs.get('yaml_path', None)
        image = 'hub-%s:latest-%s' % (app, model)

        if service == Service.Client:
            self._service_nodes[name] = dict()
            ret = self
        elif model == 'base' or yaml_path.isidentifier():
            ret = supercall()
            image = 'gnes/gnes:latest-alpine'
        else:
            # ignore invalid yaml path
            path = pathlib.Path(yaml_path)
            path.touch()
            ret = supercall()
            path.unlink()

        # add custom kwargs
        try:
            name = name if name else '%s%d' % (service, self._service_name_counter[service]-1)

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
            p_args = vars(v['parsed_args'])

            defaults_kwargs, _ = service_map[
                v['service']]['parser']().parse_known_args(['--yaml_path', 'TrainableBase'])

            non_default_kwargs = {
                k: v for k, v in p_args.items() if getattr(defaults_kwargs, k) != v}

            command = '%s %s' % (
                service_map[v['service']]['cmd'],
                ' '.join(['--%s %s' % (k, v) for k, v in non_default_kwargs.items()])
            )

            self.helm_yaml[v['app']] += [dict(
                name=k,
                app=v['app'],
                model=v['model'],
                port_in=p_args.get('port_in', None),
                port_out=p_args.get('port_out', None),
                ctrl_port=p_args.get('ctrl_port', None),
                grpc_port=p_args.get('grpc_port', None),
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

