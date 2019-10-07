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
    Class for managing a yaml as a python object.

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

    yaml['__path__'] = path
    yaml['__text__'] = __text__
    yaml['__type__'] = __type__

    import pdb;
    pdb.set_trace()
    return Box(yaml)

        # mount box attrs to Yaml instance
        # box = getattr(Box(yaml), self.__type__.name.lower())
        # for key in box:
        #     self.__dict__[key] = getattr(box, key)

    @property
    def hash(self):
        return md5(self.__text__).hexdigest()