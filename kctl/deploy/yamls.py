
import yaml
from glob import glob

INVALID_PIPELINE_PREFIXES = ('_', '.')

def yaml_safe_load(root, file):
    with open(root + '/' + file) as fh:
        return yaml.safe_load(fh)


def compile_yamls(app_path):
    import os

    yamls = dict()

    yam = yaml_safe_load(app_path, 'connections.yaml')
    yamls.update(**yam)

    pipelines = app_path + '/pipelines/'

    for pipeline in next(os.walk(pipelines))[1]:
        if not pipeline.startswith(INVALID_PIPELINE_PREFIXES):
            if 'pipelines' not in yamls:
                yamls['pipelines'] = dict()

            print(pipeline)
            stubs = yaml_safe_load(pipelines + pipeline, 'stubs.yaml')
            yamls['pipelines'][pipeline] = stubs['stubs']

    services = app_path + '/services/'
    for service in next(os.walk(services))[1]:
        if not service.startswith(INVALID_PIPELINE_PREFIXES):
            if 'services' not in yamls:
                yamls['services'] = dict()

            service = yaml_safe_load(services + service, 'services.yaml')
            yamls['services'][service] = service['service']

    import json
    print(json.dumps(yamls,indent=4))
