

from collections import defaultdict
from gnes.helper import set_logger
from importlib import machinery
from itertools import chain
from gnes.flow import Flow
from pathlib import Path
from typing import List
import subprocess
import threading
import atexit
import time
import sys
import os


THREAD_LOG_INTERVAL = 0.1


class AppManager:
    """Manager that keeps track of all of the koursaros
    paths and packages. Passed around at runtime to make
    things more efficient.

    :param base: base path to check for pipeline default=CWD
    """

    def __init__(self):
        self.root = Path(__path__).parent
        os.chdir(str(self.root))
        self.pkg_path = Path(__file__).parent
        self.logger = set_logger('kctl')

        self.threads = []
        self.thread_logs = defaultdict(lambda: [])
        self.thread_logging = False

        atexit.register(self.join)

    def find(self, *dirs: str) -> 'Path':
        check_path = self.root.joinpath(*dirs)
        if check_path.exists():
            return check_path

        raise FileNotFoundError(f'"%s" not found' % str(Path(*dirs)))

    def subprocess_call(self, cmd: List[str], shell=False):
        string = cmd if shell else ' '.join(cmd)
        self.logger.critical('subprocess.call: "%s"' % string)
        subprocess.call(cmd, shell=shell)

    def thread(self, *args, **kwargs):
        if not self.thread_logging:
            self.thread_logging = True
            self.thread(target=self.thread_logger)

        t = threading.Thread(*args, **kwargs)
        t.start()
        self.threads += [t]

    def thread_logger(self):
        while True:
            for ctx in list(self.thread_logs):
                logs = self.thread_logs.pop(ctx)
                prefix = '\n%s: ' % self.color_hash(ctx)
                to_log = prefix + ''.join(logs).rstrip().replace('\n', prefix) + '\n'
                sys.stdout.write(to_log)
            time.sleep(THREAD_LOG_INTERVAL)

    @staticmethod
    def color_hash(string: str) -> str:
        # return string with color chosen based on string
        color_ranges = [range(31, 38), range(90, 98)]
        color_choices = [color for color_range in color_ranges for color in color_range]
        return '\033[%sm%s\033[0m' % (
            color_choices[abs(hash(string)) % (len(color_choices) - 1)], string)

    def join(self):
        for t in self.threads:
            t.join()

    def get_flow(self, *dirs: str) -> 'Flow':
        flow_path = self.find(*dirs, 'flow.py')
        flow = machinery.SourceFileLoader('flow', str(flow_path)).load_module().flow
        flow.path = flow_path
        return flow
