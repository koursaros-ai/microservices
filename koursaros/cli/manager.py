

from gnes.helper import set_logger
from importlib import machinery
from gnes.flow import Flow
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
            raise FileNotFoundError(path)

    def find_model(self, app, model) -> 'Path':
        path = self.pkg_root.joinpath('hub', app, model)
        self.check_exists(path)
        return path

    def get_flow(self, name) -> 'Flow':
        os.chdir(str(self.cache))
        path = self.git_root.joinpath('flows', name, 'flow.py')
        self.check_exists(path)
        flow = machinery.SourceFileLoader('flow', path).load_module().flow
        flow.path = path
        return flow
