import logging

log = logging.getLogger("kctl")


def yaml_safe_load(yaml_path):
    import yaml

    with open(yaml_path) as fh:
        return yaml.safe_load(fh)


def get_validated_yaml(unvalidated_yaml_path, schema_yaml_path):
    import jsonschema

    unvalidated_yaml = yaml_safe_load(unvalidated_yaml_path)
    schema_yaml = yaml_safe_load(schema_yaml_path)

    try:
        jsonschema.validate(unvalidated_yaml, schema_yaml)
    except:
        log.exception(f'{unvalidated_yaml_path} is invalid')
        raise SystemExit

    return unvalidated_yaml


def get_koursaros_yaml():
    from ..constants import KOURSAROS_YAML_PATH, KOURSAROS_SCHEMA_PATH
    koursaros_yaml = get_validated_yaml(KOURSAROS_YAML_PATH, KOURSAROS_SCHEMA_PATH)
    return koursaros_yaml['koursaros']


def get_microservice_yamls(**kwargs):
    from ..constants import MICROSERVICE_SCHEMA_PATH
    from . import get_microservice_paths

    microservice_yamls = dict()
    microservice_paths = get_microservice_paths(**kwargs)

    for microservice_path in microservice_paths:
        microservice_yaml_path = f'{microservice_path}/microservice.yaml'
        microservice_yaml = get_validated_yaml(microservice_yaml_path, MICROSERVICE_SCHEMA_PATH)
        microservice_yamls[microservice_path] = microservice_yaml

    return microservice_yamls


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
        log.exception(f'\n"{stub_string}" does not match stub string regex{example}')
        quit()

    groups = groups.groups()
    groups = groups[0].split('.') + list(groups[1:])
    groups = tuple(group if group else None for group in groups)

    return groups


def get_actions_yaml():
    from ..constants import ACTIONS_YAML_PATH, ACTIONS_SCHEMA_PATH

    actions_yaml = get_validated_yaml(ACTIONS_YAML_PATH, ACTIONS_SCHEMA_PATH)
    return actions_yaml['actions']



def get_connection(connection):
    koursaros_yaml = get_koursaros_yaml()

    configs = koursaros_yaml['connections'].get(connection)
    if not configs:
        log.exception(f'"{connection}" connection not found in koursaros.yaml')
        raise SystemExit

    host = configs['host']
    port = configs['port']
    http_port = configs['http_port']
    username = configs['username']
    password = configs['password']

    return host, port, http_port, username, password


def get_actions():
    actions_yaml = get_actions_yaml()
    actions = dict()

    for action_name, stubs_config in actions_yaml.items():
        if not actions.get(action_name):
            actions[action_name] = []

        stubs_config = stubs_config['stubs']
        for pin, stub_strings in stubs_config.items():

            if isinstance(stub_strings, str):
                stub_strings = [stub_strings]

            for stub_string in stub_strings:
                stub = (pin, *parse_stub_string(stub_string))
                actions[action_name].append(stub)
    return actions


def get_action_yaml_microservices():
    actions = get_actions()
