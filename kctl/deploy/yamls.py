
import yaml
from glob import glob


def yaml_safe_load(root, file):
    with open(root + '/' + file) as fh:
        return yaml.safe_load(fh)


def compile_yamls(app_path):
    import os

    yamls = dict()

    yam = yaml_safe_load(app_path, 'connections.yaml')
    yamls.update(**yam)

    pipelines = app_path + '/pipelines/*/'
    for pipeline in glob(pipelines):
        if 'pipelines' not in yamls:
            yamls['pipelines'] = dict()

        print(pipeline)
        stubs = yaml_safe_load(pipeline, 'stubs.yaml')
        yamls['pipelines'][pipeline] = stubs['stubs']

    services = app_path + '/services/*/'
    for service in glob(services):
        if 'services' not in yamls:
            yamls['services'] = dict()

        service = yaml_safe_load(service, 'services.yaml')
        yamls['services'][service] = service['service']

    import json
    print(json.dumps(yamls,indent=4))
