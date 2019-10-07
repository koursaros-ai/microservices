from typing import Iterable, List
from subprocess import Popen
import signal
import os

BOLD = '\033[1m{}\033[0m'


def subproc(cmds: Iterable[List]):
    """Subprocess a list of commands from specified
     and cleanup procs when done...

    :param cmds: iterable of commands (commands should be list)
    """
    procs = []

    try:
        for cmd in cmds:
            if not isinstance(cmd, list):
                raise TypeError('"%s" must be list type')

            formatted = BOLD.format(' '.join(cmd))

            print(f'''Running "{formatted}"..''')
            p = Popen(cmd)
            procs.append((p, formatted))

        for p, formatted in procs:
            p.communicate()

    except KeyboardInterrupt:
        pass

    finally:
        for p, formatted in procs:

            if p.poll() is None:
                os.kill(p.pid, signal.SIGTERM)
                print(f'Killing pid {p.pid}: {formatted}')
            else:
                print(f'Process {p.pid}: "{formatted}" ended...')


def gb_free_space():
    statvfs = os.statvfs(os.getcwd())
    return statvfs.f_frsize * statvfs.f_bfree / 1e+9      # Actual number of free bytes


def batch_fn(batch_size, call_fn, items):
    buffer = []
    for item in items:
        buffer.append(item)
        if len(buffer) % batch_size == 0:
            yield call_fn(buffer), buffer
            buffer = []
    if len(buffer) > 0:
        yield call_fn(buffer), buffer


def batch_list(arr, n):
    buffer = []
    for i, item in enumerate(arr):
        buffer.append(item)
        if (i+1) % n == 0:
            yield buffer
            buffer = []
    if len(buffer) > 0:
        yield buffer
