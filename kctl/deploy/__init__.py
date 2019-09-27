import importlib.util


def run_service(app_path, service):
    spec = importlib.util.spec_from_file_location(
        service, f'{app_path}/services/{service}/__init__.py'
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

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
        print(f'Joining process {p.pid}: {service}')
        p.join()
