import logging
import os

log = logging.getLogger("kctl")

COMMIT_MESSAGE = '.'


def git_push(**kwargs):
    from koursaros.utils import get_microservice_paths
    microservice_paths = get_microservice_paths(**kwargs)

    from git import remote, Repo
    from koursaros.constants import GIT_PATH, ACTIONS_YAML_PATH, PROTOS_PATH

    repo = Repo(f'{GIT_PATH}/.git')

    class Progress(remote.RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            log.info(self._cur_line)

    def git_add(path):
        log.info(f'Adding {microservice_paths}')
        repo.git.add([microservice_path])

    git_add(ACTIONS_YAML_PATH)
    git_add(PROTOS_PATH)

    for microservice_path in microservice_paths:
        git_add(microservice_path)

    repo.index.commit(COMMIT_MESSAGE)
    origin = repo.remote(name='origin')
    origin.push(progress=Progress())


def create_microservice(args):
    from ..boilerplate import HELLO_TEMPLATE, MICROSERVICE_TEMPLATE
    from koursaros.constants import MICROSERVICES_PATH
    import os

    print(args.microservices)

    for microservice in args.microservices:
        microservice_path = f'{MICROSERVICES_PATH}/{microservice}'
        os.makedirs(microservice_path)

        init_settings = {
            'microservice' : microservice
        }

        with open(f'{microservice_path}/__init__.py', 'w') as fh:
            if not args.model:
                fh.write(HELLO_TEMPLATE.format(**init_settings))

        microservice_settings = {
            "microservice" : microservice,
            "registry" : os.environ.get('CONTAINER_REGISTRY'),
            "base_image" : args.base_image,
            "dependencies" : "pip install --upgrade pip"
        }

        microservice_yaml = MICROSERVICE_TEMPLATE.format(**microservice_settings)
        with open(microservice_path + '/microservice.yaml', 'w') as fh:
            fh.write(microservice_yaml)

        log.info(f'Created {microservice_path}.')


def build_dockerfile(**kwargs):
    from koursaros.utils.yamls import get_microservice_yamls
    microservice_yamls = get_microservice_yamls(**kwargs)

    for microservice_path, microservice_yaml in microservice_yamls.items():
        microservice_yaml = microservice_yaml['microservice']

        envs = ''
        if 'environment' in microservice_yaml:
            for env, value in microservice_yaml['environment'].items():
                envs += f'ENV {env}={value}\n'

        deps = ''
        if 'deps' in microservice_yaml:
            for dep in microservice_yaml['deps']:
                deps += f'RUN {dep}\n'

        from ..constants import DOCKERFILE_TEMPLATE
        dockerfile = DOCKERFILE_TEMPLATE.format(
            image=microservice_yaml['from'],
            envs=envs,
            deps=deps,
            entrypoint=microservice_yaml['entrypoint']
        )

        transpiled_path = f'{microservice_path}/transpiled'

        import os
        os.makedirs(transpiled_path, exist_ok=True)
        dockerfile_path = f'{transpiled_path}/Dockerfile'

        log.info(f'Saving {dockerfile_path}')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile)


def build_deployment(tag, **kwargs):
    from koursaros.utils.yamls import get_microservice_yamls
    microservice_yamls = get_microservice_yamls(**kwargs)

    for microservice_path, microservice_yaml in microservice_yamls.items():
        microservice_name = microservice_path.split('/')[-1]
        microservice_yaml = microservice_yaml['microservice']

        node_selector = '{}'
        if 'accelerator' in microservice_yaml:
            node_selector = microservice_yaml['accelerator']

        resource_limits = '{}'
        if 'resource_limits' in microservice_yaml:
            resource_limits = microservice_yaml['resource_limits']

        strategy_type = 'RollingUpdate'
        if 'strategy_type' in microservice_yaml:
            strategy_type = microservice_yaml['strategy_type']

        from ..constants import DEPLOYMENT_TEMPLATE, PVC_TEMPLATE
        deployment = DEPLOYMENT_TEMPLATE.format(
            microservice=microservice_name,
            image=microservice_yaml['image'],
            replicas=microservice_yaml['replicas'],
            tag=tag,
            resource_limits=resource_limits,
            node_selector=node_selector,
            strategy_type=strategy_type
        )

        if 'volume' in microservice_yaml:
            volume = microservice_yaml['volume']
            if 'size' in microservice_yaml:
                size = microservice_yaml['size']
            else:
                size = '10Gi'

            deployment += PVC_TEMPLATE.format(volume=volume, size=size)

        transpiled_path = f'{microservice_path}/transpiled'

        import os
        os.makedirs(transpiled_path, exist_ok=True)
        deployment_path = f'{transpiled_path}/deployment.yaml'
        log.info(f'Saving {deployment_path}')
        with open(deployment_path, 'w') as f:
            f.write(deployment)


def template(microservice):
    import json
    t = {
        "filename": f"koursaros/microservices/{microservice}/transpiled/cloudbuild.yaml",
        "includedFiles": [
            f"koursaros/microservices/{microservice}/**",
            "koursaros/microservices/base.py"
        ],
        "name": f"{microservice}",
        "triggerTemplate": {
            "repoName": "github_koursaros_ai_koursaros",
            "projectId": "---",
            "branchName": ".*"
        },
        "description": f"{microservice}"
    }
    return json.dumps(t)


def get_gcloud_headers():
    from subprocess import Popen, PIPE
    cmd = ['gcloud', "config", "config-helper", "--format", 'value(credential.access_token)']
    p = Popen(cmd, stdout=PIPE)
    output, _ = p.communicate()
    bearer_token = output.decode('utf-8').strip()
    headers = {'Authorization': f'Bearer {bearer_token}'}
    return headers


def build_trigger(**kwargs):
    import json
    import requests
    from koursaros.utils import get_microservice_names

    headers = get_gcloud_headers()
    microservices = get_microservice_names(**kwargs)
    for microservice in microservices:
        data = template(microservice)
        r = requests.post(url=TRIGGERS_API, data=data, headers=headers)
        j = json.loads(r.content)
        if 'error' in j:
            log.warning(j['error']['message'])
        else:
            log.info(f'{microservice} trigger created.')


def list_triggers(headers):
    import json
    import requests
    headers = get_gcloud_headers()
    r = requests.get(url=TRIGGERS_API, headers=headers)
    triggers = json.loads(r.content)['triggers']
    return {trigger['name']: trigger['id'] for trigger in triggers}


def delete_trigger(**kwargs):
    import json
    import requests
    from koursaros.utils import get_microservice_names
    headers = get_gcloud_headers()
    microservices = get_microservice_names(**kwargs)
    triggers = list_triggers(headers)
    triggers = {name: id for name, id in triggers.items() if name in microservices}

    for trigger, id in triggers.items():
        api = TRIGGERS_API + id
        r = requests.delete(url=api, headers=headers)
        j = json.loads(r.content)
        m = json.dumps(j, indent=4)
        if 'error' in j:
            log.exception(m)
        else:
            log.info(f'{trigger} trigger deleted.')


def build_cloudbuild(tag, **kwargs):
    from koursaros.utils.yamls import get_validated_yaml, get_microservice_yamls
    from koursaros.constants import KOURSAROS_YAML_PATH, KOURSAROS_SCHEMA_PATH

    koursaros_yaml = get_validated_yaml(KOURSAROS_YAML_PATH, KOURSAROS_SCHEMA_PATH)
    koursaros_yaml = koursaros_yaml['koursaros']

    microservice_yamls = get_microservice_yamls(**kwargs)

    for microservice_path, microservice_yaml in microservice_yamls.items():
        microservice_name = microservice_path.split('/')[-1]
        microservice_yaml = microservice_yaml['microservice']
        transpiled_path = f'{microservice_path}/transpiled'

        import os
        os.makedirs(transpiled_path, exist_ok=True)
        cloudbuild_yaml_path = f'{transpiled_path}/cloudbuild.yaml'

        from ..constants import CLOUDBUILD_TEMPLATE
        cloudbuild = CLOUDBUILD_TEMPLATE.format(
            microservice=microservice_name,
            tag=tag,
            zone=koursaros_yaml['kubernetes']['zone'],
            cluster=koursaros_yaml['kubernetes']['cluster'],
            image=microservice_yaml['image']
        )

        log.info(f'Saving {cloudbuild_yaml_path}')
        with open(cloudbuild_yaml_path, 'w') as fh:
            fh.write(cloudbuild)

