

def bind_rabbitmq(
        pipeline, stubs,
        host='localhost', port=5672,
        http_port=15672, username='root', password=None):

    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    http_string = f'vhost "{pipeline}" on {BOLD.format(url)}'
    pika_string = f'vhost "{pipeline}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(pipeline)
    except requests.exceptions.HTTPError:
        print(f'Not found: {http_string}')

    print(f'Creating {http_string}')
    api.create_vhost(pipeline)
    api.create_user_permission(username, pipeline)

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, pipeline, credentials)
    connection = pika.BlockingConnection(parameters=parameters)  # pika connection
    channel = connection.channel()

    print(f'Creating exchange "nyse" on {pika_string}')
    channel.exchange_declare(exchange='nyse', exchange_type='direct')

    for stub in stubs:
        pin, service, func, _, _, _ = stub
        queue = f'{service}.{func}'
        print(f'Creating user "{pipeline}" on {http_string}')
        api.create_user(service, password)
        api.create_user_permission(service, pipeline)

        print(f'Creating queue "{queue}" on {pika_string}')
        channel.queue_declare(queue=queue, durable=True)

        print(f'Binding "{pin}" to "{queue}" queue on {pika_string}')
        channel.queue_bind(exchange='nyse', queue=queue, routing_key=pin)

