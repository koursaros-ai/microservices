
from subprocess import Popen
import signal
import sys
import os


def deploy_pipeline(pipe_path, args):
    app_name = pipe_path.split('/')[-2]
    os.chdir(pipe_path + '..')

    processes = []
    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline)

    try:
        for service in pipeline.services.names:
            cmd = [sys.executable, '-m', f'{app_name}.services.{service}'] + sys.argv[1:]
            print(f'Running {cmd}...')
            p = Popen(cmd)
            processes.append((p, service))

        for p, service in processes:
            p.communicate()

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(exc)

    finally:
        for p, service in processes:

            if p.poll() is None:
                os.kill(p.pid, signal.SIGTERM)
                print(f'Killing pid {p.pid}: {service}')
            else:
                print(f'process {p.pid}: "{service}" ended...')