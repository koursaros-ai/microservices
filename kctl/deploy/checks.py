

CHECK_TIMEOUT = 10


def check_stubs(args):

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    pipeline = pipeline(args.pipeline_name)

    for service in pipeline.services:
        for stub in service.stubs:
            if stub._OutProto and not stub._InProto:
                raise ValueError(f'"{stub.__name__}" is sending "{stub._InProto.__class__.__name__}" proto to nothing...')

            receiving_stub = False if stub._out_stub else True
            for service2 in pipeline.services:
                for stub2 in service2.stubs:
                    if stub2.__name__ == stub._out_stub.__name__:
                        receiving_stub = True
                        if stub2._InProto != stub._OutProto:
                            raise ValueError(
                                f'{stub.__name__} is sending "{stub._OutProto.__class__.__name__}" proto,'
                                f'but {stub2.__name__} is receiving "{stub2._InProto.__class__.__name__}" proto')

            if not receiving_stub:
                raise ValueError(f'no receiving stub for "{stub.__name__}"')


def check_rabbitmq(args):
    import pika
    from ..utils import BOLD

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    pipeline = pipeline(args.pipeline_name)
    connection = pipeline.active_connection

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

