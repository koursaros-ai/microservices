from pathlib import Path
import random
from collections import defaultdict
from base64 import b64encode
import ruamel

APPS = ['httpclient', 'frontend', 'router', 'preprocessor', 'encoder', 'indexer']
IN_SOCKS = ['PULL', 'SUB', 'RPC']
OUT_SOCKS = ['PUSH', 'PUB', 'RPC']


def parse_line(line):
    try:
        line = [x.strip() for x in line.split('|')]

        if len(line) != 8:
            raise ValueError('Expected %s columns on line: %s' % (8, line))

        if not line[0].isnumeric():
            raise ValueError('expected numeric id but got %s' % line[0])
        id = int(line[0])

        app = line[1]
        if not app in APPS:
            raise ValueError('app must be in %s not %s' % (APPS, line[1]))

        model = line[2] if line[2] else None
        if model and not model.isidentifier():
            raise ValueError('model must be python identifier "%s"' % line[2])

        image = 'hub-%s:latest-%s' % (app, model) if model else 'gnes/gnes:latest-alpine'

        if not line[3].isnumeric():
            raise ValueError('replicas must be numeric not "%s"' % line[3])
        reps = int(line[3])

        yaml_path = line[4] if line[4] else None

        i = line[5].split(':')
        if len(i) != 2:
            raise ValueError('":" not found in %s' % i)
        if i[0] not in IN_SOCKS:
            raise ValueError('"%s" not in %s' % (i[0], IN_SOCKS) )
        if i[1] and not i[1].isnumeric():
            raise ValueError('in sock "%s" is not numeric' % i[1])
        i[1] = int(i[1]) if i[1] else None
        i[0] += '_CONNECT' if i[1] else '_BIND'

        o = line[6].split(':')
        if len(o) != 2:
            raise ValueError('":" not found in %s' % o)
        if o[0] not in OUT_SOCKS:
            raise ValueError('"%s" not in %s' % (o[0], OUT_SOCKS) )
        if o[1] and not o[1].isnumeric():
            raise ValueError('out sock "%s" is not numeric' % o[1])
        o[1] = int(o[1]) if o[1] else None
        o[0] += '_CONNECT' if o[1] else '_BIND'

        command = line[7] if line[7] else None

        return vars()

    except ValueError as e:
        raise ValueError('Error on line: %s\n\n%s' % (line, e))


class Flow:
    def __init__(self, path: 'Path'):
        self.services = dict()
        self.ports = defaultdict(
            lambda: {'ins': set(), 'outs': set()})
        self.path = path
        self.lines = []
        self.p = list(range(53001, 65001))
        random.shuffle(self.p)

        with Path(path).open() as fh:
            for line in fh:
                self.add_line(line)

    def add_line(self, line: str):
        if not line.strip().startswith('#'):
            self.lines += [line]
            service = parse_line(line)
            self._add_service(service)

    def _add_service(self, s: dict):
        in_id = s['i'][1]
        if in_id:
            self.ports[in_id]['outs'].add(s['id'])

        out_id = s['o'][1]
        if out_id:
            self.ports[out_id]['ins'].add(s['id'])

        s['name'] = s['model'] + str(s['id']) if s['model'] else s['app'] + str(s['id'])
        s['local_in'] = self.p.pop()
        s['local_out'] = self.p.pop()
        self.services[s['id']] = s

    @property
    def swarm(self):
        y = {'version': 3.4, 'services': {}}
        for s in self.services.values():
            new = dict(volumes='./.cache:/workspace')
            new['command'] = [s['command']] if s['command'] else []
            new['command'] += ['--socket_in', s['i'][0], '--socket_out', s['o'][0]]

            if s['app'] == 'frontend':
                new['ports'] = ['80:80']

            if s['yaml_path']:
                new['command'] += ['--yaml_path', s['yaml_path']]

            # if connecting in
            in_id = s['i'][1]
            if in_id:
                new['command'] += ['--host_in', self.services[in_id]['name']]
                new['command'] += ['--port_in', self.services[in_id]['local_out']]
            # if binding in
            else:
                new['command'] += ['--port_in', s['local_in']]

            # if connecting out
            out_id = s['o'][1]
            if out_id:
                new['command'] += ['--host_out', self.services[out_id]['name']]
                new['command'] += ['--port_out', self.services[out_id]['local_in']]
            # if binding out
            else:
                new['command'] += ['--port_out', s['local_out']]

            new['command'] = ' '.join([str(x) for x in new['command']])
            y['services'][s['name']] = new

        return ruamel.yaml.dump(y)

    @property
    def mermaid_url(self):
        app_colors = dict(
            httpclient=('#FFE0E0', '#000', '1px'),
            frontend=('#FFE0E0', '#000', '1px'),
            router=('#C9E8D2', '#000', '1px'),
            encoder=('#FFDAAF', '#000', '1px'),
            preprocessor=('#CED7EF', '#000', '1px'),
            indexer=('#FFFBC1', '#000', '1px'),
        )

        lines = ['graph TD']
        for cls, fmt in app_colors.items():
            lines += ['classDef {} fill:{},stroke:{},stroke-width:{};'.format(cls, *fmt)]

        def edge(left_s, right_s):
            return ['{ln}--{lt}-{rt}-->{rn}'.format(
                ln=left_s['name'],
                lt=left_s['o'][0],
                rt=right_s['i'][0],
                rn=right_s['name']
            )]

        for bound_id, port in self.ports.items():
            bound_s = self.services[bound_id]
            # lines += ['subgraph %s' % bound_s['name']]

            for conn_id in port['ins']:
                conn_s = self.services[conn_id]
                lines += edge(conn_s, bound_s)

            for conn_id in port['outs']:
                conn_s = self.services[conn_id]
                lines += edge(bound_s, conn_s)

            # lines += ['end']

        for s in self.services.values():
            lines += ['class {} {};'.format(s['name'], s['app'])]

        return 'https://mermaidjs.github.io/mermaid-live-editor/#/view/' + b64encode('\n'.join(lines).encode()).decode()



