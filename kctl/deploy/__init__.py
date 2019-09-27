import sys


def run_service(app_path, service):
    sys.path.insert(1, app_path)
    from .services import pig
    raise SystemExit

    module = __import__(service, fromlist=['.services'])
    service = getattr(module.services, service)

    main = getattr(service, 'main', None)
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
