
from pathlib import Path
from gnes.helper import set_logger
from typing import Tuple, List
import subprocess
import threading
import atexit
import time
import sys
from collections import defaultdict

THREAD_LOG_INTERVAL = 0.1


class AppManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self, base: str = '.'):
        self.base = Path(base).absolute()
        self.pkg_path = Path(__file__).parent
        self.cache_path = self.pkg_path.joinpath('.cache')
        self.logger = set_logger('KCTL')
        try:
            self.app_paths = set(self.cache_path.read_text().split('\n'))
        except FileNotFoundError:
            self.app_paths = set()
        self.root = self.find_root()
        self.threads = []
        self.thread_logs = defaultdict(lambda: [])
        self.thread_logging = False

        atexit.register(self.join)

    def find_root(self) -> 'Path':
        if self.base.joinpath('.kctl').is_dir():
            return self.base
        for path in self.base.parents:
            if path.joinpath('.kctl').is_dir():
                self.app_paths.add(str(path))
                self.cache()
                return path

    def cache(self):
        self.cache_path.write_text('\n'.join(self.app_paths))

    def find_app_file(self, *dirs: Tuple[str]) -> 'Path':
        _ = self.root
        for path in self.app_paths:
            check_path = Path(path).joinpath(*dirs)
            print(check_path)
            if check_path.is_file():
                return check_path

        raise FileNotFoundError(f'"%s" not found' % str(Path(*dirs)))

    def raise_if_no_app_roots(self):
        if self.app_paths == set():
            raise NotADirectoryError(f'"%s" is not an app' % self.base)

    def subprocess_call(self, cmd: List[str]):
        self.logger.critical('subprocess.call: "%s"' % ' '.join(cmd))
        subprocess.call(cmd)

    def thread(self, *args, **kwargs):
        if not self.thread_logging:
            self.thread_logging = True
            self.thread(target=self.thread_logger)

        t = threading.Thread(*args, **kwargs)
        t.start()
        self.threads += [t]

    def thread_logger(self):
        while True:
            for ctx, logs in self.thread_logs.items():
                sys.stdout.write(''.join(logs).replace('\n', '\n%s' % ctx))
            self.thread_logs.clear()
            time.sleep(THREAD_LOG_INTERVAL)

    def join(self):
        for t in self.threads:
            t.join()

