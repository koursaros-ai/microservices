

def bind_rabbitmq(args):

    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    koursaros = __import__(f'koursaros.pipelines.{args.pipeline}')
    pipeline = getattr(getattr(koursaros.pipelines, args.pipeline), args.pipeline)
    connection = getattr(pipeline.connections, args.connection)

    host = connection.host
    http_port = connection.http_port
    port = connection.port
    username = connection.username
    password = connection.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    http_string = f'vhost "{pipeline}" on {BOLD.format(url)}'
    pika_string = f'vhost "{pipeline}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(pipeline.name)
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

    for service_name in pipeline.services.names:
        service = getattr(pipeline.services, service_name)
        for stub_name in service.stubs.names:
            queue = service_name + '.' + stub_name
            print(f'Creating user "{pipeline}" on {http_string}')
            api.create_user(service_name, password)
            api.create_user_permission(service_name, pipeline.name)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{stub_name}" to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=stub_name)

