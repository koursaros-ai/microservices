import os
# from kctl.utils import BOLD
from subprocess import Popen
import signal

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

def subproc(cmds):
    """Subprocess a list of commands from specified
     directories and cleanup procs when done

    :param cmds: iterable list of tuples (directory, cmd)
    """
    procs = []

    try:
        for path, cmd in cmds:
            os.chdir(path)
            # formatted = BOLD.format(' '.join(cmd))
            formatted = ' '.join(cmd)

            print(f'''Running "{formatted}" from "{path}"...''')
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
