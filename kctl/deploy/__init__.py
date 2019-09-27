import sys
from subprocess import Popen
import os
import signal
import time

ONE_DAY_IN_SECONDS = 60 * 60 * 24

def deploy_pipelines(app_path, services):

    app_name = app_path.split('/')[-2]
    os.chdir(app_path + '..')
    pids = []
    try:
        for service in services:
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}']
            p = Popen(cmd)
            pids.append((p.pid, service))
            while True:
                time.sleep(ONE_DAY_IN_SECONDS)

    except Exception as exc:
        print(exc)
        for pid, service in pids:
            print(f'Killing pid {pid}: {service}')
            os.kill(pid, signal.SIGTERM)
