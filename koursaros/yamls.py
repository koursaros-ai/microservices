from yaml import safe_load
from hashlib import md5
from enum import Enum
from box import Box


class YamlType(Enum):
    BASE = 0
    PIPELINE = 1
    SERVICE = 2


class Yaml(Box):
    """
    Class for managing a yaml as a python object.

    :param path: path to .yaml file
    """
    def __init__(self, path):
        self.__path__ = path
        self.__text__ = open(path).read()

        if 'base' in self.__yaml__:
            self.__type__ = YamlType.BASE
        elif 'pipeline' in self.__yaml__:
            self.__type__ = YamlType.PIPELINE
        elif 'service' in self.__yaml__:
            self.__type__ = YamlType.SERVICE
        else:
            raise ValueError('Invalid yaml type for %s' % self.__path__)

        super().__init__(safe_load(self.__text__))

    @property
    def hash(self):
        return md5(self.__text__).hexdigest()