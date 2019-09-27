import importlib.util
from threading import Thread


def run_service(app_path, service, stubs):
    spec = importlib.util.spec_from_file_location(
        service, f'{app_path}/services/{service}/__init__.py'
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    main = getattr(module, 'main', None)
    if main:
        main()

    threads = []
    for stub in stubs:
        t = Thread(target=getattr(module, stub, None).consume)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def deploy_pipelines(app_path, services):
    from multiprocessing import Process

    processes = []
    for service, stubs in services.items():
        p = Process(
            target=run_service,
            args=(app_path, service, stubs)
        )
        p.start()
        print(f'Started process {p.pid}: {service}...')
        processes.append((p, service))
    for p, service in processes:
        print(f'Joining process {p.pid}: {service}')
        p.join()
