
from koursaros.utils.yamls import get_actions
from logging import getLogger

CHECK_TIMEOUT = 10

ACTION_MATCH = r'^[a-zA-Z0-9_]*$'
PIN_MATCH = r'^[a-zA-Z0-9_]*$'
MICROSERVICE_MATCH = r'^[a-z]*$'
FUNC_MATCH = r'^[a-zA-Z]*$'
PROTO_MATCH = r'^[a-zA-Z0-9_]*$'

DOES_NOT_SATISFY = '''
{what} naming does satisfy naming requirements:
\t1. Microservice names must contain only lowercase letters.
\t2. Function names must have only alphanumeric characters.
\t3. Pin, action, and proto names must have only alphanumeric or underscore characters.
'''


def check_stubs(app_path):
    import re
    import json

    yamls = app_path + '/.koursaros/yamls.json'

    for pipeline, stubs in json.load(open(yamls))['pipelines'].items():
        pins_in = set()
        pins_out = set()
        pins = dict()
        invalid_names = set()
        not_getting_protos = set()

        for pin_in, microservice, func_name, proto_in, proto_out, pin_out in stubs:

            if microservice not in valid_microservices:
                log.exception(f'{microservice} not found in {MICROSERVICES_PATH}')
                raise SystemExit

            if proto_out and not pin_out:
                log.exception(f'{pin_in} is sending "{proto_out}" proto to nothing...')
                raise SystemExit

            if not proto_in:
                not_getting_protos.add(pin_in)

            if not re.match(ACTION_MATCH, action):
                invalid_names.add(f'"{action}" action')
            if not re.match(PIN_MATCH, pin_in):
                invalid_names.add(f'"{pin_in}" pin')
            if not re.match(MICROSERVICE_MATCH, microservice):
                invalid_names.add(f'"{microservice}" microservice')
            if not re.match(FUNC_MATCH, func_name):
                invalid_names.add(f'"{func_name}" function')
            if proto_in and not re.match(PROTO_MATCH, proto_in):
                invalid_names.add(f'"{proto_in}" proto')
            if proto_out and not re.match(PROTO_MATCH, proto_out):
                invalid_names.add(f'"{proto_out}" proto')
            if proto_out and not re.match(PIN_MATCH, pin_out):
                invalid_names.add(f'"{pin_out}" pin')

            pins_in.add(pin_in)
            if pin_out:
                pins_out.add(pin_out)
            pins[pin_in] = (proto_in, proto_out, pin_out)

        if invalid_names:
            log.exception(DOES_NOT_SATISFY.format(what=', '.join(invalid_names)))
            raise SystemExit

        missing_pins = pins_out - pins_in
        not_receiving = (pins_in - pins_out) - not_getting_protos

        if missing_pins:
            log.exception(f'no receiving pins for {missing_pins} in {action}')
            raise SystemExit
        if not_receiving:
            log.exception(f'no pins sending to: {not_receiving} in {action}')
            raise SystemExit

        for pin in pins:
            pin_out = pins[pin][2]
            sending_proto = pins[pin][1]
            if pin_out:
                receiving_proto = pins[pin_out][0]
                if not receiving_proto == sending_proto:
                    log.exception(f'''
                        {pin} in {action} is sending "{sending_proto}" proto,
                        but {pin_out} is receiving "{receiving_proto}" proto
                    ''')
                    raise SystemExit


def check_protos():

    protos = set()
    module = __import__('koursaros.protos').protos

    for action, stubs in get_actions().items():
        for (_, _, _, proto_in, proto_out, _) in stubs:
            if proto_in:
                protos.add(proto_in)
            if proto_out:
                protos.add(proto_out)

        for proto in protos:
            if not getattr(module, proto, None):
                log.exception(f'"{proto}" proto in actions.yaml not found in {module.__name__}')
                raise SystemExit


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
