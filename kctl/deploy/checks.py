

CHECK_TIMEOUT = 10


def check_stubs(args):

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline)

    for service_name in pipeline.services.names:
        service = getattr(pipeline.services, service_name)
        for stub_name in service.stubs.names:
            stub = getattr(service.stubs, stub_name)

            if stub.proto_out and not stub.stub_out:
                raise ValueError(f'"{stub.name}" is sending "{stub.proto_out}" proto to nothing...')

            receiving_stub = False if stub.stub_out else True
            for stub2_name in service.stubs.names:
                stub2 = getattr(service.stubs, stub2_name)
                print('NAME:',stub2)
                if stub2.name == stub.stub_out:
                    receiving_stub = True
                    if stub2.proto_in != stub.proto_out:
                        raise ValueError(
                            f'{stub.name} is sending "{stub.proto_out}" proto,'
                            f'but {stub2.name} is receiving "{stub2.proto_in}" proto')

            if not receiving_stub:
                raise ValueError(f'no receiving stub for "{stub.name}"')


def check_rabbitmq(args):
    import pika
    from ..utils import BOLD

    koursaros = __import__(f'koursaros.pipelines.{args.pipeline}')
    pipeline = getattr(getattr(koursaros.pipelines, args.pipeline), args.pipeline)
    connection = getattr(pipeline.connections, args.connection)

    host = connection.host
    port = connection.port
    username = connection.username
    password = connection.password

    bold_ip = BOLD.format(f'{host}:{port}')

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                blocked_connection_timeout=CHECK_TIMEOUT,
                host=host,
                port=port,
                credentials=pika.PlainCredentials(
                    username=username,
                    password=password
                )
            )
        )
        print(f'Successful rabbitmq connection: {bold_ip}')
        channel = connection.channel()
        print(f'Successful rabbitmq channel: {bold_ip}')
        connection.close()
    except Exception as exc:
        from sys import platform

        print(f'Failed pika connection on: {bold_ip}\n{exc.args}')

        if platform == "linux" or platform == "linux2":
            import distro

            dist, version, codename = distro.linux_distribution()
            if dist in ('Ubuntu', 'Debian'):
                print('Please install rabbitmq:\n\n' +
                      BOLD.format('sudo apt-get install rabbitmq-server -y --fix-missing\n'))

            elif dist in ('RHEL', 'CentOS', 'Fedora'):
                print('Please install rabbitmq:\n\n' +
                      BOLD.format('wget https://www.rabbitmq.com/releases/'
                                  'rabbitmq-server/v3.6.1/rabbitmq-server-3.6.1-1.noarch.rpmn\n'
                                  'sudo yum install rabbitmq-server-3.6.1-1.noarch.rpm\n'))
            else:
                print('Please install rabbitmq')

        elif platform == "darwin":
            print('Please install rabbitmq:\n\n' +
                  BOLD.format('brew install rabbitmq\n'))

        elif platform == "win32":
            print('Please install rabbitmq:\n\n' +
                  BOLD.format('choco install rabbitmq\n'))
            raise NotImplementedError

        raise SystemExit

