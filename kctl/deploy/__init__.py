import importlib.util
import sys


def run_service(app_path, service):

    sys.path.insert(0, app_path)

    print(sys.path)

    # mod = __import__('.services', fromlist=['pig'])

    from .services import pig
    print(dir(pig))
    raise SystemExit

    spec = importlib.util.spec_from_file_location(f'.', app_path)
    print(dir(spec))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    print(dir(module))
    raise SystemExit

    main = getattr(module, 'main', None)
    if main:
        main()


def deploy_pipelines(app_path, services):
    from multiprocessing import Process

    processes = []
    for service in services:
        p = Process(
            target=run_service,
            args=(app_path, service)
        )
        p.start()
        print(f'Started process {p.pid}: {service}...')
        processes.append((p, service))
    for p, service in processes:
        p.join()
        print(f'Joining process {p.pid}: {service}')
