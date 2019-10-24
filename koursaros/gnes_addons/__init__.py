from gnes.flow import *
import pathlib
import functools
from gnes.cli.parser import set_client_http_parser
from gnes.client.http import HttpClient

_Flow = Flow
DEFAULT_IMAGE = 'gnes/gnes:latest-alpine'


class Service(BetterEnum):
    Frontend = 0
    Encoder = 1
    Router = 2
    Indexer = 3
    Preprocessor = 4
    HTTPClient = 5


service_map[Service.HTTPClient] = dict(
    parser=set_client_http_parser,
    builder=HttpClient,
    cmd='client http'
)


class Flow(_Flow):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.client_node = {}

    def add_client(self, *args, **kwargs):
        # self.client_node = dict(
        #     app='client',
        #     model=kwargs['name'],
        #     image='hub-client:latest-%s' % kwargs['name'],
        #     yaml_path=kwargs['yaml_path'],
        #     replicas=kwargs.get('replicas', None)
        # )
        return self.add(Service.HTTPClient, *args, **kwargs)

    def add(self, service: Union['Service', str], name: str = None, *args, **kwargs):
        supercall = functools.partial(super().add, service, name, *args, **kwargs)
        app = service.name.lower()
        model = name if name else 'base'
        yaml_path = kwargs.get('yaml_path', None)

        if model == 'base' or yaml_path.isidentifier():
            ret = supercall()
            image = DEFAULT_IMAGE
        else:
            # ignore invalid yaml path
            path = pathlib.Path(yaml_path)
            path.touch()
            ret = supercall()
            path.unlink()
            image = 'hub-%s:latest-%s' % (app, model)

        # add custom kwargs
        name = name if name else '%s%d' % (service, ret._service_name_counter[service]-1)
        # import pdb; pdb.set_trace()
        v = ret._service_nodes[name]
        v['storage'] = kwargs.get('storage', '500Mi')
        v['memory'] = kwargs.get('storage', '500Mi')
        v['cpu'] = kwargs.get('storage', '300m')
        v['replicas'] = kwargs.get('replicas', 1)
        v['app'] = app
        v['model'] = model
        v['image'] = image

        return ret

    @staticmethod
    def yaml_stream(yml):
        from ruamel.yaml import YAML, StringIO
        _yaml = YAML()
        stream = StringIO()
        _yaml.dump(yml, stream)
        return stream.getvalue().strip()

    @build_required(BuildLevel.GRAPH)
    def get_service_command(self, name):
        svc = self._service_nodes[name]

        defaults_kwargs, _ = service_map[svc['service']]['parser']().parse_known_args(
            ['--yaml_path', 'TrainableBase'])

        p_args = vars(svc['parsed_args'])
        # remove default kwargs
        for k, v in vars(defaults_kwargs).items():
            if v == p_args.get(k, None):
                p_args.pop(k, None)

        if not isinstance(p_args.get('yaml_path', ''), str):
            p_args['yaml_path'] = svc['kwargs']['yaml_path']

        command = '' if svc['image'] != DEFAULT_IMAGE else service_map[svc['service']]['cmd'] + ' '
        command += ' '.join(['--%s %s' % (k, v) for k, v in p_args.items()])
        return command

    @build_required(BuildLevel.GRAPH)
    def to_swarm_yaml(self) -> str:
        """
        Generate the docker swarm YAML compose file
        :return: the generated YAML compose file
        """

        swarm_yml = {'version': '3.4',
                     'services': {}}

        for name, node in self._service_nodes.items():
            swarm_yml['services'][name] = dict(
                image=node['image'],
                command=self.get_service_command(name)
            )
            if node['replicas'] > 1:
                swarm_yml['services'][name]['deploy'] = {'replicas': node['replicas']}
            grpc_port = vars(node['parsed_args']).get('grpc_port', None)
            if grpc_port:
                swarm_yml['services'][name]['ports'] = ['%s:%s' % (grpc_port, grpc_port)]

        return self.yaml_stream(swarm_yml)

    @build_required(BuildLevel.GRAPH)
    def to_helm_yaml(self):
        self.helm_yaml = defaultdict(lambda: [])

        for name, node in self._service_nodes.items():
            command = self.get_service_command(name)
            p_args = vars(node['parsed_args'])

            self.helm_yaml[node['app']] += [dict(
                name=name,
                app=node['app'],
                model=node['model'],
                port_in=p_args.get('port_in', None),
                port_out=p_args.get('port_out', None),
                ctrl_port=p_args.get('ctrl_port', None),
                grpc_port=p_args.get('grpc_port', None),
                command=command.split(),
                replicas=node['replicas'],
                storage=node['storage'],
                memory=node['memory'],
                cpu=node['cpu'],
                image=node['image']
            )]

        self.helm_yaml = dict(services=dict(self.helm_yaml))
        return self.yaml_stream(self.helm_yaml)

    @build_required(BuildLevel.GRAPH)
    def to_mermaid(self, left_right: bool = True) -> str:
        """
        Output the mermaid graph for visualization
        :param left_right: render the flow in left-to-right manner, otherwise top-down manner.
        :return: a mermaid-formatted string
        """

        # fill, stroke
        service_color = {
            Service.Frontend: ('#FFE0E0', '#000'),
            Service.Router: ('#C9E8D2', '#000'),
            Service.Encoder: ('#FFDAAF', '#000'),
            Service.Preprocessor: ('#CED7EF', '#000'),
            Service.Indexer: ('#FFFBC1', '#000'),
        }

        mermaid_graph = OrderedDict()
        cls_dict = defaultdict(set)
        replicas_dict = {}

        for k, v in self._service_nodes.items():
            mermaid_graph[k] = []
            num_replicas = getattr(v['parsed_args'], 'num_parallel', 1)
            if num_replicas > 1:
                head_router = k + '_HEAD'
                tail_router = k + '_TAIL'
                replicas_dict[k] = (head_router, tail_router)
                cls_dict[Service.Router].add(head_router)
                cls_dict[Service.Router].add(tail_router)
                p_r = '((%s))'
                k_service = v['service']
                p_e = '((%s))' if k_service == Service.Router else '(%s)'

                mermaid_graph[k].append('subgraph %s["%s (replias=%d)"]' % (k, k, num_replicas))
                for j in range(num_replicas):
                    r = k + '_%d' % j
                    cls_dict[k_service].add(r)
                    mermaid_graph[k].append('\t%s%s-->%s%s' % (head_router, p_r % 'router', r, p_e % r))
                    mermaid_graph[k].append('\t%s%s-->%s%s' % (r, p_e % r, tail_router, p_r % 'router'))
                mermaid_graph[k].append('end')
                mermaid_graph[k].append(
                    'style %s fill:%s,stroke:%s,stroke-width:2px,stroke-dasharray:5,stroke-opacity:0.3,fill-opacity:0.5' % (
                        k, service_color[k_service][0], service_color[k_service][1]))

        for k, ed_type in self._service_edges.items():
            start_node, end_node = k.split('-')
            cur_node = mermaid_graph[start_node]

            s_service = self._service_nodes[start_node]['service']
            e_service = self._service_nodes[end_node]['service']

            start_node_text = start_node
            end_node_text = end_node

            # check if is in replicas
            if start_node in replicas_dict:
                start_node = replicas_dict[start_node][1]  # outgoing
                s_service = Service.Router
                start_node_text = 'router'
            if end_node in replicas_dict:
                end_node = replicas_dict[end_node][0]  # incoming
                e_service = Service.Router
                end_node_text = 'router'

            # always plot frontend at the start and the end
            if e_service == Service.Frontend:
                end_node_text = end_node
                end_node += '_END'

            cls_dict[s_service].add(start_node)
            cls_dict[e_service].add(end_node)
            p_s = '((%s))' if s_service == Service.Router else '(%s)'
            p_e = '((%s))' if e_service == Service.Router else '(%s)'
            cur_node.append('\t%s%s-- %s -->%s%s' % (
                start_node, p_s % start_node_text, ed_type,
                end_node, p_e % end_node_text))

        style = ['classDef %sCLS fill:%s,stroke:%s,stroke-width:1px;' % (k, v[0], v[1]) for k, v in
                 service_color.items()]
        class_def = ['class %s %sCLS;' % (','.join(v), k) for k, v in cls_dict.items()]
        mermaid_str = '\n'.join(
            ['graph %s' % ('LR' if left_right else 'TD')] + [ss for s in mermaid_graph.values() for ss in
                                                             s] + style + class_def)

        return mermaid_str