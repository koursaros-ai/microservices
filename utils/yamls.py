from yaml import safe_load
from hashlib import md5
from enum import Enum
from box import Box


class YamlType(Enum):
    BASE = 0
    PIPELINE = 1
    SERVICE = 2


def Yaml(path):
    """
    Sudo class for managing a yaml as a python object.

    :param path: path to .yaml file
    """
    __type__ = None
    __text__ = open(path).read()
    yaml = safe_load(__text__)

    for yaml_type in YamlType:
        if yaml_type.name.lower() in yaml:
            __type__ = yaml_type

    if __type__ is None:
        raise ValueError('Invalid yaml type for %s' % path)

    box = Box(yaml[__type__.name.lower()])
    box.__path__ = path
    box.__text__ = __text__
    box.__type__ = __type__
    box.hash = md5(__text__.encode()).hexdigest()
    return box
