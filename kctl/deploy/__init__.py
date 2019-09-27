import sys


def run_service(app_path, service, imports):

    sys.path.insert(0, app_path)

    module = __import__('services', fromlist=[service])

    print(dir(module))
    print('HOLA')

    for _import in imports:
        module.setattr(module, _import, __import__(_import))

    print(dir(module))
    raise SystemExit
    main = getattr(getattr(module, service), 'main', None)
    if main:
        main()


def deploy_pipelines(app_path, services, imports):
    from multiprocessing import Process
    from threading import Thread

    processes = []
    for service in services:
        p = Thread(
            target=run_service,
            args=(app_path, service, imports)
        )
        p.start()
        print(f'Started process {p.getName()}: {service}...')
        processes.append((p, service))
    for p, service in processes:
        p.join()
        print(f'Joining process {p.getName()}: {service}')
