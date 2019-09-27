from .yamls import get_validated_yaml, get_actions, get_koursaros_yaml
import logging

log = logging.getLogger(__name__)


def unpack(object):
    import inspect

    print(f"{'-'*10} Dirs {'-'*10}")
    for att in dir(object):
        print(f'{att}: {getattr(object, att, None)}')
    print(f"{'-'*10} Args {'-'*10}")
    print(inspect.getfullargspec(object))


def get_directories(path):
    import os
    return set(next(os.walk(path))[1])


def get_microservice_paths(microservices=set(), all=False):
    from ..constants import MICROSERVICES_PATH, INVALID_YAML_DIR_PREFIXES

    valid_microservices = get_directories(MICROSERVICES_PATH)
    valid_microservices = [m for m in valid_microservices \
                           if not m.startswith(INVALID_YAML_DIR_PREFIXES)]

    if not all:
        microservice_paths = set()

        for microservice in microservices:
            if microservice.startswith(INVALID_YAML_DIR_PREFIXES):
                log.exception(f'"{microservice}" directory name is invalid')
                quit()

            if microservice not in valid_microservices:
                log.exception(f'"{microservice}" directory not found in {MICROSERVICES_PATH}')
                quit()
            microservice_paths.add(f'{MICROSERVICES_PATH}/{microservice}')

        return microservice_paths
    return [f'{MICROSERVICES_PATH}/{m}' for m in valid_microservices]


def get_microservice_names(**kwargs):
    microservice_paths = get_microservice_paths(**kwargs)
    return {microservice_path.split('/')[-1] for microservice_path in microservice_paths}


def get_hypers(file):
    import os
    from ..constants import MICROSERVICE_SCHEMA_PATH
    from ..protos import Hyper, Group, Groups
    location = os.path.dirname(file)
    microservice_yaml = get_validated_yaml(
        f'{location}/microservice.yaml',
        MICROSERVICE_SCHEMA_PATH
    )
    microservice = file.split('/')[-2]
    groups_proto = Groups()
    groups = microservice_yaml['microservice']['hypers']['groups']
    for group, hypers in groups.items():
        group_proto = Group(name=group, microservice=microservice)
        for hyper, configs in hypers.items():
            hyper_proto = Hyper(name=hyper)
            for key, value in configs.items():
                if key == 'bounds':
                    hyper_proto.bounds.extend(value)
                elif key == 'choices':
                    hyper_proto.choices.extend(value)
                else:
                    setattr(hyper_proto, key, value)
            group_proto.hypers.extend([hyper_proto])
        groups_proto.groups.extend([group_proto])

    return groups_proto
