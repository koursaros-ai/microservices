

from gnes.helper import set_logger
from importlib import machinery
from koursaros.flow import Flow
from pathlib import Path
from typing import List
import subprocess
import git
import os


class AppManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param dev: run on local koursaros repo
    """

    def __init__(self):
        self.git_root = Path(git.Repo(
            '.', search_parent_directories=True).working_tree_dir)
        self.pkg_root = Path(__file__).parent.parent

        self.logger = set_logger('kctl')
        self.cache = self.git_root.joinpath('.k')
        self.cache.mkdir(exist_ok=True)

    def call(self, cmd: List[str], shell=False):
        string = cmd if shell else ' '.join(cmd)
        self.logger.critical('subprocess.call: "%s"' % string)
        subprocess.call(cmd, shell=shell)

    @staticmethod
    def check_exists(path: 'Path'):
        if not path.exists():
            raise FileNotFoundError(path.absolute())

    def find_model(self, app: str, model: str) -> 'Path':
        path = self.pkg_root.joinpath('hub', app, model)
        self.check_exists(path)
        return path

    def get_flow(self, path) -> 'Flow':
        path = Path(path)
        self.check_exists(path)
        return Flow(path)
