import sys


def run_service(app_path, service, _imports):

    sys.path.insert(0, app_path)

    module = __import__('services', fromlist=[service])

    for _import in _imports:
        name = _import.__name__
        print(f'Importing {name} to {service}...')
        setattr(module, name, _import)

    main = getattr(getattr(module, service), 'main', None)
    if main:
        main()


def deploy_pipelines(app_path, services, fairseq):
    # from multiprocessing import Process
    from threading import Thread

    _imports = [fairseq]
    # for import_ in imports:
    #     _imports.append(__import__(import_))

    processes = []
    for service in services:
        p = Thread(
            target=run_service,
            args=(app_path, service, _imports)
        )
        p.start()
        print(f'Started process {p.getName()}: {service}...')
        processes.append((p, service))
    for p, service in processes:
        p.join()
        print(f'Joining process {p.getName()}: {service}')
