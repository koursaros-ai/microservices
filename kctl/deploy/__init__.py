import importlib.util


def run_service(app_path, pipelines, service, connection_name, **connection):
    spec = importlib.util.spec_from_file_location(
        service, f'{app_path}/services/{service}/__init__.py'
    )
    print(f'{app_path}/services/{service}')
    print(spec)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(pipelines, connection_name, **connection)


def deploy_pipelines(app_path, pipelines, services, connection_name, **connection):
    from multiprocessing import Process

    processes = []
    for service in services:
        p = Process(
            target=run_service,
            args=(app_path, pipelines, service, connection_name),
            kwargs=connection
        )
        p.start()
        print(f'Started process {p.pid}: {service}...')
        processes.append((p, service))
    for p, service in processes:
        print(f'Joining process {p.pid}: {service}')
        p.join()
