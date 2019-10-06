from koursaros import Type
from pathlib import Path
from hashlib import md5

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


class AppManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self, base: str = '.'):
        self.base = Path(base).absolute()
        self.pkg_path = Path(__import__('koursaros').__path__[0])
        self.lookup_path = [self.root, self.pkg_path]

    @property
    def root(self):
        for path in self.base.parents:
            if path.joinpath('.kapp').is_dir():
                return path

    def search_for_yaml_path(self, name: str, type: Type):
        """
        Given a particular type of entity and its name, find
        the directory and path to its yaml (if applicable)

        Each type name is designated in the name of the yaml.
        For example, the elastic service should be in
        services => elastic.yaml...

        This rule has one exception: bases
        Each base is named according to its directory.
        For example, the elastic base should be in
        bases => elastic => base.yaml

        :param name: the name of the type
        :param type: the type
        """
        for path in self.lookup_path:

            # if type is base then find yaml in base dir
            if type == Type.BASE:
                parent_dir = 'bases'
                name = 'base'

            elif type == Type.PIPELINE:
                parent_dir = 'pipelines'

            elif type == Type.SERVICE:
                parent_dir = 'services'

            elif type == Type.BUILD:
                parent_dir = 'build'

            else:
                raise TypeError('Invalid type: %s' % type)

            search_yaml_path = path.joinpath(parent_dir).joinpath(name).with_suffix('.yaml')

            if search_yaml_path.is_file():
                return search_yaml_path


    @staticmethod
    def hash_files(paths):
        return [md5(open(path, 'rb').read()).hexdigest() for path in paths]

    def raise_if_app_root(self):
        if self.root is not None:
            raise IsADirectoryError(f'"{self.base}" is already a pipeline')

    def raise_if_no_app_root(self):
        if self.root is None:
            raise NotADirectoryError(f'"{self.base}" is not a pipeline')