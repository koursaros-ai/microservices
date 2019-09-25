
def bind_rabbitmq(desired_actions, host, port, http_port, username, password):
    from koursaros.utils.yamls import get_actions
    from koursaros.constants import BOLD
    from .api import AdminAPI
    import requests
    import logging
    import pika

    log = logging.getLogger('kctl')

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    actions = get_actions()
    for action in desired_actions:

        try:
            stubs = actions.pop(action)
        except KeyError:
            log.exception(f'\n\n\nAction not found in actions.yaml: "{action}"\n\n')
            raise SystemExit
        http_string = f'vhost "{action}" on {BOLD.format(url)}'
        pika_string = f'vhost "{action}" on {BOLD.format(ip)}'

        try:
            api.delete_vhost(action)
            log.info(f'Deleted {http_string}')
        except requests.exceptions.HTTPError as exc:
            log.info(f'Not found: {http_string}')
        except:
            log.exception(f'Failed deleting {http_string}')
            raise SystemExit

        try:
            api.create_vhost(action)
            api.create_user_permission(username, action)
            log.info(f'Created {http_string}')
        except:
            log.exception(f'Failed creating {http_string}')
            raise SystemExit

        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host, port, action, credentials)
        connection = pika.BlockingConnection(parameters=parameters)  # pika connection
        channel = connection.channel()

        channel.exchange_declare(exchange='nyse', exchange_type='direct')
        log.info(f'Created exchange "nyse" on {pika_string}')

        for stub in stubs:
            pin, service, func, _, _, _ = stub
            queue = f'{service}.{func}'
            try:
                api.create_user(service, password)
                api.create_user_permission(service, action)
                log.info(f'Created user "{action}" on {http_string}')
            except:
                log.exception(f'Failed creating user on {http_string}')
                raise SystemExit

            channel.queue_declare(queue=queue, durable=True)
            log.info(f'Created queue "{queue}" on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=pin)
            log.info(f'Bound "{pin}" to "{queue}" queue on {pika_string}')
