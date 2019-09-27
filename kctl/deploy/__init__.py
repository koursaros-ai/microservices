import sys
from subprocess import Popen
import os
import signal


def deploy_pipelines(app_path, services):

    app_name = app_path.split('/')[-1]
    sys.path.append(app_path + '/..')

    pids = []
    try:
        for service in services:
            p = Popen([sys.executable, '-m', f'{app_name}.services.{service}'])
            pids.append((p.pid, service))

    except Exception as exc:
        print(exc)
        for pid, service in pids:
            print(f'Killing pid {pid}: {service}')
            os.kill(pid, signal.SIGTERM)
