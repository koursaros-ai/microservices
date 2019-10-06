
from importlib import reload
from pathlib import Path
from hashlib import md5
import yaml as pyyaml
import os


BOLD = '\033[1m{}\033[0m'


def decorator_group(options):
    """returns a decorator which bundles the given decorators

    :param options: iterable of decorators
    :return: single decorator

    Example:
        deploy_options = option_group([
            click.option('-c', '--connection', required=True),
            click.option('-r', '--rebind', is_flag=True),
            click.option('-d', '--debug', is_flag=True),
        ])

    """
    def option_decorator(f):
        for option in options:
            f = option(f)
        return f
    return option_decorator


class PipelineYaml:
    def __init__(self, path):
        super().__init__()
        self.yaml = pyyaml.safe_load(open(path))
        self.path = path
        self.services = []

        for serv_name, configs in self.yaml['pipeline'].items():
            if configs is not None:
                # service = Box(configs)
                service.name = serv_name
                self.check_null(service, 'push')
                self.check_null(service, 'pull')
                self.check_null(service, 'callback')
                self.services.append(service)

    @staticmethod
    def check_null(obj, attr):
        """Set attribute to the string "null" if it does not exist"""
        if not hasattr(obj, attr):
            setattr(obj, attr, 'null')


class Manager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self, base='.'):
        self.base = Path(base).absolute()
        x = self.kapp
        import pdb; pdb.set_trace()
        self.app_root = Path(self.find_app_root())
        self.kapp_path = self.app_root + '.kapp'
        import koursaros
        self.koursaros = koursaros
        self.kpath = Path(koursaros.__path__[0])
        self.pipe_path = [self.app_root + 'pipelines', self.kpath + 'pipelines']
        self.serv_path = [self.app_root + 'services', self.kpath + 'services']

        if self.app_root is not None:
            self.app_name = self.kpath[-1]

    def get_pipe_yaml(self, pipe_yaml):
        for path in self.pipe_path:
            pipe_yamls = self.get_next(path, suffix='.yaml', option=2)

            if pipe_yaml in pipe_yamls:
                return PipelineYaml((path + pipe_yaml).tostring())

        return None

    def get_serv_path(self, serv_name):

        for path in self.serv_path:

            serv_names = self.get_next(path, option=1)

            if serv_name in serv_names:
                return (path + serv_name).tostring()

        return None

    def reload(self):
        reload(self.koursaros)
        self.__init__()

    @property
    def kapp(self):
        for path in self.base.parents:
            kapp = path.with_name('.kapp')
            if kapp.is_dir():
                return kapp

        return None

    @staticmethod
    def get_next(path, option=1, suffix=None):
        """Returns directories for a path

        :param path: Path object
        :param option: 1 = directories, 2 = files
        :param suffix: suffix to filter with (filetype)
        :return: (name, path) tuples
        """
        try:
            names = next(os.walk(path.tostring()))[option]
        except StopIteration:
            return [tuple()]

        filtered = [name for name in names if name[0] not in '_.']
        if suffix is not None:
            filtered = [name for name in names if name.endswith(suffix)]

        return filtered
        # return dict(zip(filtered, [path + name for name in filtered]))

    @staticmethod
    def get_files(path):
        dir_names = next(os.walk(path))[2]
        filtered = [name for name in dir_names if name[0] not in '_.']
        return dict(zip(filtered, [path + name for name in filtered]))

    @staticmethod
    def hash_files(paths):
        return [md5(open(path, 'rb').read()).hexdigest() for path in paths]

    def raise_if_app_root(self):
        if self.app_root is not None:
            raise IsADirectoryError(f'"{self.base}" is already a pipeline')

    def raise_if_no_app_root(self):
        if self.app_root is None:
            raise NotADirectoryError(f'"{self.base}" is not a pipeline')