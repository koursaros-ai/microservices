
from koursaros import pipelines
from importlib import reload
from hashlib import md5
import kctl
import os

BOLD = '\033[1m{}\033[0m'


def cls(obj):
    return obj.__class__.__name__


def option_group(options):
    """returns a decorator which bundles the given click options

    :param options: iterable of click.options
    :return: click option decorator

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


class PathManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self, base=os.getcwd()):
        self.base = base
        self.pipe_root = self.find_pipe_root()
        self.pipelines = pipelines
        self.compile_path = pipelines.__path__[0] + '/'
        self.existing_pipes = self.get_dirs(self.compile_path)
        self.kctl_path = kctl.__path__[0] + '/'
        self.kctl_create_path = self.kctl_path + '/create/template/pipeline/'

        if self.pipe_root is not None:
            self.pipe_name = self.pipe_root.split('/')[-2]
            self.pipe = self.load_pipe()
            self.pipe_save_dir = self.compile_path + self.pipe_name
            self.pipe_save_file = f'{self.pipe_save_dir}/__init__.py'
            self.conn_path = self.pipe_root + '/connections.yaml'
            self.stubs_path = self.pipe_root + '/stubs.yaml'
            self.serv_dirs = self.get_dirs(self.pipe_root + 'services/')
            self.serv_paths = {name: path + '/service.yaml' for name, path in self.serv_dirs.items()}
            self.conn_hash = self.hash_files([self.conn_path])[0]
            self.stubs_hash = self.hash_files([self.stubs_path])[0]
            self.serv_hashes = self.hash_files(
                [self.serv_paths[name] for name in sorted(self.serv_paths)]
            )

    def reload_pipelines(self):
        reload(self.pipelines)
        self.pipe = self.load_pipe()

    def load_pipe(self):
        pipe = getattr(pipelines, self.pipe_name, None)
        return pipe() if pipe is not None else None

    def find_pipe_root(self):
        current_path = ''
        for directory in self.base.split('/'):
            current_path += directory + '/'
            test_path = current_path + '.koursaros'
            if os.path.isdir(test_path):
                return current_path

        return None

    @staticmethod
    def get_dirs(path):
        """Returns directories for a path

        :param path: filepath
        :return: (dir names, dir paths)
        """
        dir_names = next(os.walk(path))[1]
        filtered = [name for name in dir_names if name[0] not in '_.']
        return dict(zip(filtered, [path + name for name in filtered]))

    @staticmethod
    def hash_files(paths):
        return [md5(open(path, 'rb').read()).hexdigest() for path in paths]

    def raise_if_pipe_root(self):
        if self.pipe_root is not None:
            raise IsADirectoryError(f'"{self.base}" is already a pipeline')

    def raise_if_no_pipe_root(self):
        if self.pipe_root is None:
            raise NotADirectoryError(f'"{self.base}" is not a pipeline')