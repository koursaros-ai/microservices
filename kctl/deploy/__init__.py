

from subprocess import Popen
from kctl.utils import BOLD
import signal
import sys
import os


def deploy_pipeline(pipe_path, args):
    app_name = pipe_path.split('/')[-2]
    os.chdir(pipe_path + '..')

    processes = []
    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    pipeline = pipeline(None)

    try:
        for service in pipeline.services:
            service_cls = service.__class__.__name__
            cmd = [sys.executable, '-m', f'{app_name}.services.{service_cls}'] + sys.argv[1:]
            print(f'''Running "{BOLD.format(' '.join(cmd))}"...''')
            p = Popen(cmd)
            processes.append((p, service_cls))

        for p, service_cls in processes:
            p.communicate()

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(exc)

    finally:
        for p, service_cls in processes:

            if p.poll() is None:
                os.kill(p.pid, signal.SIGTERM)
                print(f'Killing pid {p.pid}: {service_cls}')
            else:
                print(f'process {p.pid}: "{service_cls}" ended...')