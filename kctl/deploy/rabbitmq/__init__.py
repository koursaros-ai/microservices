

def bind_rabbitmq(pm, connection):
    from kctl.utils import cls
    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    conn = getattr(pm.pipe.Connections, connection)

    host = conn.host
    http_port = conn.http_port
    port = conn.port
    username = conn.username
    password = conn.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    http_string = f'vhost "{pm.pipe_name}" on {BOLD.format(url)}'
    pika_string = f'vhost "{pm.pipe_name}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(pm.pipe_name)
    except requests.exceptions.HTTPError:
        print(f'Not found: {http_string}')

    print(f'Creating {http_string}')
    api.create_vhost(pm.pipe_name)
    api.create_user_permission(username, pm.pipe_name)

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, pm.pipe_name, credentials)
    connection = pika.BlockingConnection(parameters=parameters)  # pika connection
    channel = connection.channel()

    print(f'Creating exchange "nyse" on {pika_string}')
    channel.exchange_declare(exchange='nyse', exchange_type='direct')

    for service in pm.pipe.Services:
        for stub in service.Stubs:
            queue = cls(stub)
            user = cls(service) + '.' + cls(stub)
            vhost = pm.pipe_name

            print(f'Creating user "{user}" on {http_string}')
            api.create_user(user, password)
            api.create_user_permission(user, vhost)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{queue}" stub to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=queue)

