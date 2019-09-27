import sys
from subprocess import Popen
import os
import signal


def deploy_pipelines(app_path, services):

    app_name = app_path.split('/')[-2]
    sys.path.append(app_path + '..')
    print(sys.path)
    pids = []
    try:
        for service in services:
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}']
            print(cmd)
            p = Popen(cmd)
            pids.append((p.pid, service))

    except Exception as exc:
        print(exc)
        for pid, service in pids:
            print(f'Killing pid {pid}: {service}')
            os.kill(pid, signal.SIGTERM)
