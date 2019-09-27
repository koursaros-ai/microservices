
import json

CHECK_TIMEOUT = 10


def check_stubs(services, stubs):

    pins_in = set()
    pins_out = set()
    pins = dict()

    for pin_in, service, func_name, proto_in, proto_out, pin_out in stubs:

        if service not in services.keys():
            raise ValueError(f'{service} service not found.')

        if proto_out and not pin_out:
            raise ValueError(f'{pin_in} is sending "{proto_out}" proto to nothing...')

        pins_in.add(pin_in)
        if pin_out:
            pins_out.add(pin_out)
        pins[pin_in] = (proto_in, proto_out, pin_out)

    missing_pins = pins_out - pins_in

    if missing_pins:
        raise ValueError(f'no receiving pins for {missing_pins}')

    for pin in pins:
        pin_out = pins[pin][2]
        sending_proto = pins[pin][1]
        if pin_out:
            receiving_proto = pins[pin_out][0]
            if not receiving_proto == sending_proto:
                raise ValueError(
                    f'{pin} is sending "{sending_proto}" proto,'
                    f'but {pin_out} is receiving "{receiving_proto}" proto'
                )


def check_protos(app_path, stubs):
    import sys
    sys.path.append(app_path + '/.koursaros')
    protos = set()
    module = __import__('messages_pb2')

    for stub in stubs:
        proto_in = stub[3]
        proto_out = stub[4]
        if proto_in:
            protos.add(proto_in)
        if proto_out:
            protos.add(proto_out)

    for proto in protos:
        if not getattr(module, proto, None):
            raise ModuleNotFoundError(f'"{proto}" proto not found in {module.__name__}')


def check_rabbitmq(host='localhost', port=5672, username='root', password=None, **kwargs):
    import pika
    from ..utils import BOLD

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

