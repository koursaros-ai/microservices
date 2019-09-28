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
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}'] + sys.argv[1:]
            print(f'Running {cmd}...')
            popen = Popen(cmd)
            popens.append((popen, service))

        for popen, service in popens:
            popen.communicate()

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(exc)

    finally:
        for popen, service in popens:

            if popen.poll() is None:
                os.kill(popen.pid, signal.SIGTERM)
                print(f'Killing pid {popen.pid}: {service}')
            else:
                print(f'process {popen.pid}: "{service}" ended...')