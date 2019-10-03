

def bind_rabbitmq(args):
    from kctl.utils import cls
    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    pipeline = pipeline(None)

    connection = pipeline.Connections.getactive()

    host = connection.host
    http_port = connection.http_port
    port = connection.port
    username = connection.username
    password = connection.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    http_string = f'vhost "{cls(pipeline)}" on {BOLD.format(url)}'
    pika_string = f'vhost "{cls(pipeline)}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(cls(pipeline))
    except requests.exceptions.HTTPError:
        print(f'Not found: {http_string}')

    print(f'Creating {http_string}')
    api.create_vhost(cls(pipeline))
    api.create_user_permission(username, cls(pipeline))

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, cls(pipeline), credentials)
    connection = pika.BlockingConnection(parameters=parameters)  # pika connection
    channel = connection.channel()

    print(f'Creating exchange "nyse" on {pika_string}')
    channel.exchange_declare(exchange='nyse', exchange_type='direct')

    for service in pipeline.Services:
        for stub in service.Stubs:
            queue = cls(stub)
            user = cls(service) + '.' + cls(stub)
            vhost = cls(pipeline)

            print(f'Creating user "{user}" on {http_string}')
            api.create_user(user, password)
            api.create_user_permission(user, vhost)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{queue}" stub to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=queue)

