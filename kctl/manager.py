
from koursaros.yamls import YamlType
from pathlib import Path


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

    def search_for_yaml_path(self, name: str, yaml_type: YamlType):
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
        :param yaml_type: the type
        """
        for path in self.lookup_path:

            # if type is base then find yaml in base dir
            if yaml_type == YamlType.BASE:
                parent_dir = 'bases'
                name = 'base'

            elif yaml_type == YamlType.PIPELINE:
                parent_dir = 'pipelines'

            elif yaml_type == YamlType.SERVICE:
                parent_dir = 'services'

            else:
                raise TypeError('Invalid type: %s' % yaml_type)

            search_yaml_path = path.joinpath(parent_dir).joinpath(name).with_suffix('.yaml')

            if search_yaml_path.is_file():
                return search_yaml_path

    def raise_if_app_root(self):
        if self.root is not None:
            raise IsADirectoryError(f'"{self.base}" is already a pipeline')

    def raise_if_no_app_root(self):
        if self.root is None:
            raise NotADirectoryError(f'"{self.base}" is not a pipeline')