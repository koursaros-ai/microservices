
import yaml
import os
import json

INVALID_PIPELINE_PREFIXES = ('_', '.')


def yaml_safe_load(root, file):
    with open(root + '/' + file) as fh:
        return yaml.safe_load(fh)


def parse_stub_string(stub_string):
    import re
    s = r'\s*'
    ns = r'([^\s]*)'
    nsp = r'([^\s]+)'
    full_regex = rf'{s}{nsp}\({s}{ns}{s}\){s}->{s}{ns}{s}\|{s}{ns}{s}'
    full_regex = re.compile(full_regex)
    example = '\nExample: <service>( [variable] ) -> <returns> | <destination>'
    groups = full_regex.match(stub_string)

    if not groups:
        raise ValueError(f'\n"{stub_string}" does not match stub string regex{example}')

    groups = groups.groups()
    groups = groups[0].split('.') + list(groups[1:])
    groups = tuple(group if group else None for group in groups)

    return groups


def compile_yamls(app_path):
    yamls = dict()

    yam = yaml_safe_load(app_path, 'connections.yaml')
    yamls.update(**yam)

    pipelines = app_path + '/pipelines/'

    for pipeline in next(os.walk(pipelines))[1]:
        if not pipeline.startswith(INVALID_PIPELINE_PREFIXES):
            if 'pipelines' not in yamls:
                yamls['pipelines'] = dict()

            if pipeline not in yamls['pipelines']:
                yamls['pipelines'][pipeline] = []

            stubs = yaml_safe_load(pipelines + pipeline, 'stubs.yaml')

            for pin, stub_strings in stubs['stubs'].items():

                if isinstance(stub_strings, str):
                    stub_strings = [stub_strings]

                for stub_string in stub_strings:
                    stub = (pin, *parse_stub_string(stub_string))
                    yamls['pipelines'][pipeline].append(stub)

    services = app_path + '/services/'
    for service in next(os.walk(services))[1]:
        if not service.startswith(INVALID_PIPELINE_PREFIXES):
            if 'services' not in yamls:
                yamls['services'] = dict()

            yam = yaml_safe_load(services + service, 'service.yaml')
            yamls['services'][service] = yam['service']

    with open(app_path + '/.koursaros/yamls.json', 'w') as fh:
        fh.write(json.dumps(yamls, indent=4))

    return yamls

