
from pathlib import Path
from gnes.helper import set_logger

class AppManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self, base: str = '.'):
        self.base = Path(base).absolute()
        self.pkg_path = Path(__import__('koursaros').__path__[0])
        self.logger = set_logger('KCTL')

    @property
    def root(self):
        if self.base.joinpath('.kctl').is_dir():
            return self.base
        for path in self.base.parents:
            if path.joinpath('.kctl').is_dir():
                return path

    def raise_if_not_app_root(self):
        if self.root is None:
            raise NotADirectoryError(f'"%s" is not an app' % self.base)