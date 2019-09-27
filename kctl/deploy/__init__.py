import importlib.util
from threading import Thread


def run_service(app_path, service, stubs):
    spec = importlib.util.spec_from_file_location(
        service, f'{app_path}/services/{service}/__init__.py'
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    threads = []

    for stub in stubs:
        print(module.service.stubs.__dict__)
        stub_cls = getattr(module.service.stubs, stub, None)
        print(dir(stub_cls))
        raise SystemExit
        t = Thread(target=stub_cls.consume,)
        print(f'Starting thread {t.getName()}: {stub}')
        t.start()
        threads.append((t, stub))

    main = getattr(module, 'main', None)
    if main:
        main()

    for t, what in threads:
        print(f'Joining thread {t.getName()}: "{what}"')
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
