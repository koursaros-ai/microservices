import sys
from subprocess import Popen, PIPE, STDOUT
import os
import signal
from threading import Thread


def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''): # b'\n'-separated lines
        print(line)


def deploy_pipelines(app_path, services):
    app_name = app_path.split('/')[-2]
    os.chdir(app_path + '..')
    popens = []
    threads = []
    try:
        for service in services:
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}']
            print(f'Running {cmd}...')
            popen = Popen(cmd, stdout=PIPE,  stderr=STDOUT)

            with popen.stdout:
                t = Thread(target=log_subprocess_output, args=(popen.stdout,))
                t.start()
                threads.append(t)

            popens.append((popen, service))

        for popen, service in popens:
            popen.communicate()

    except KeyboardInterrupt:
        pass

    finally:
        for popen, service in popens:

            if popen.poll() is None:
                os.kill(popen.pid, signal.SIGTERM)
                print(f'Killing pid {popen.pid}: {service}')
            else:
                print(f'process {popen.pid}: "{service}" ended...')