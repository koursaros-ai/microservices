from yaml import safe_load
from enum import Enum
from box import Box


class Type(Enum):
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
        self.__yaml__ = safe_load(open(path))
        self.__version__ = self.__yaml__.pop('version')

        if 'base' in self.__yaml__:
            self.__type__ = Type.BASE
        elif 'pipeline' in self.__yaml__:
            self.__type__ = Type.PIPELINE
        elif 'service' in self.__yaml__:
            self.__type__ = Type.SERVICE
        else:
            raise ValueError('Invalid yaml type for %s' % self.__path__)

        super().__init__(self.__yaml__)