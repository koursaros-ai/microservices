
CHECK_TIMEOUT = 10


def check_stubs(app, args):

    for pipeline in args.pipelines:
        stubs = app.pipelines[pipeline].stubs.items()
        for stub in stubs:

            if stub.service not in app.services:
                raise ValueError(f'{stub.service} service not found.')

            if stub.proto_out and not stub.stub_out:
                raise ValueError(f'{stub.name} is sending "{stub.proto_out}" proto to nothing...')

            receiving_stub = False
            for stub_2 in stubs:
                if stub_2.name == stub.stub_out:
                    receiving_stub = True
                    if stub_2.proto_in != stub.proto_out:
                        raise ValueError(
                            f'{stub.name} is sending "{stub.proto_out}" proto,'
                            f'but {stub_2.name} is receiving "{stub_2.proto_in}" proto')

            if not receiving_stub:
                raise ValueError(f'no receiving stub for {stub.name}')


def check_rabbitmq(app, args):
    import pika
    from ..utils import BOLD

    host = app.connection.host
    port = app.connection.port
    username = app.connection.username
    password = app.connection.password

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

