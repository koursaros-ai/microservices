

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

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self):
        self.git_root = Path(git.Repo('.', search_parent_directories=True).working_tree_dir)
        self.pkg_root = Path(__file__).parent.parent
        self.logger = set_logger('kctl')
        self.cache = self.git_root.joinpath('.k')
        self.cache.mkdir(exist_ok=True)
        os.chdir(str(self.cache))

    def find(self, *dirs: str, pkg=False) -> 'Path':
        search_path = self.pkg_root if pkg else self.git_root
        check_path = search_path.joinpath(*dirs)
        if check_path.exists():
            return check_path

        raise FileNotFoundError(f'"%s" not found' % str(Path(*dirs)))

    def call(self, cmd: List[str], shell=False):
        string = cmd if shell else ' '.join(cmd)
        self.logger.critical('subprocess.call: "%s"' % string)
        subprocess.call(cmd, shell=shell)

    def find_model(self, app, model) -> 'Path':
        return self.find('koursaros/hub', app, model)

    def get_flow(self, name) -> 'Flow':
        path = self.find('koursaros', 'flows', name, 'flow.py')
        flow = machinery.SourceFileLoader('flow', str(path)).load_module().flow
        flow.path = path
        return flow
