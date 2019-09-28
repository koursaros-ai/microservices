import sys
from subprocess import Popen
import os
import signal


def deploy_pipelines(app, args):
    app_name = app.path.split('/')[-2]
    os.chdir(app.path + '..')

    popens = []

    # get only the services having to do with pipelines
    services = set()
    for pipeline in args.pipelines:
        services |= {stub.service for stub in app.pipelines[pipeline].stubs.values()}

    services = {service for service in app.pipelines}
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