
import json

CHECK_TIMEOUT = 10


def check_stubs(app_path, pipeline):
    yamls_path = app_path + '/.koursaros/yamls.json'

    yamls = json.load(open(yamls_path))
    stubs = yamls['pipelines'][pipeline].values()

    pins_in = set()
    pins_out = set()
    pins = dict()
    not_getting_protos = set()

    for pin_in, service, func_name, proto_in, proto_out, pin_out in stubs:

        if service not in yamls['services'].keys():
            raise ValueError(f'{service} service not found.')

        if proto_out and not pin_out:
            raise ValueError(f'{pin_in} is sending "{proto_out}" proto to nothing...')

        if not proto_in:
            not_getting_protos.add(pin_in)

        pins_in.add(pin_in)
        if pin_out:
            pins_out.add(pin_out)
        pins[pin_in] = (proto_in, proto_out, pin_out)

    missing_pins = pins_out - pins_in
    not_receiving = (pins_in - pins_out) - not_getting_protos

    if missing_pins:
        raise ValueError(f'no receiving pins for {missing_pins} in {pipeline}')
    if not_receiving:
        raise ValueError(f'no pins sending to: {not_receiving} in {pipeline}')

    for pin in pins:
        pin_out = pins[pin][2]
        sending_proto = pins[pin][1]
        if pin_out:
            receiving_proto = pins[pin_out][0]
            if not receiving_proto == sending_proto:
                raise ValueError(
                    f'{pin} in {pipeline} is sending "{sending_proto}" proto,'
                    f'but {pin_out} is receiving "{receiving_proto}" proto'
                )


def check_protos(app_path, pipeline):
    import sys
    sys.path.append(app_path + '/.koursaros')
    protos = set()
    module = __import__('messages_pb2')

    yamls_path = app_path + '/.koursaros/yamls.json'
    yamls = json.load(open(yamls_path))
    stubs = yamls['pipelines'][pipeline].values()

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


def check_rabbitmq(host, port, http_port, username, password):
    import pika
    from koursaros.constants import BOLD

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
        log.info(f'Successful pika connection: {bold_ip}')
        channel = connection.channel()
        log.info(f'Successful pika channel: {bold_ip}')
        connection.close()
    except Exception as exc:
        log.exception(f'Failed pika connection on: {bold_ip}\n{exc.args}')
        raise SystemExit
