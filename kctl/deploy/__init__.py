import sys
from subprocess import Popen
import os
import signal


def deploy_pipelines(app_path, services):

    app_name = app_path.split('/')[-2]
    os.chdir(app_path + '..')
    popens = []
    try:
        for service in services:
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}']
            print(f'Starting {cmd}...')
            popen = Popen(cmd)
            popens.append((popen, service))

        for popen, service in popens:
            popen.communicate()
            print(f'process {popen.pid}: "{service}" ended...')

    except KeyboardInterrupt as exc:
        print(exc)
        for popen, service in popens:
            print(f'Killing pid {popen.pid}: {service}')
            os.kill(popen.pid, signal.SIGTERM)
