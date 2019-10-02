

def bind_rabbitmq(args):

    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    connection = getattr(pipeline.connections, args.connection)

    host = connection.host
    http_port = connection.http_port
    port = connection.port
    username = connection.username
    password = connection.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    http_string = f'vhost "{pipeline.__name__}" on {BOLD.format(url)}'
    pika_string = f'vhost "{pipeline.__name__}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(pipeline.name)
    except requests.exceptions.HTTPError:
        print(f'Not found: {http_string}')

    print(f'Creating {http_string}')
    api.create_vhost(pipeline.name)
    api.create_user_permission(username, pipeline.name)

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, pipeline.name, credentials)
    connection = pika.BlockingConnection(parameters=parameters)  # pika connection
    channel = connection.channel()

    print(f'Creating exchange "nyse" on {pika_string}')
    channel.exchange_declare(exchange='nyse', exchange_type='direct')

    for service in pipeline.services:
        for stub in service.stubs:
            queue = service.__name__ + '.' + stub.__name__
            print(f'Creating user "{service.__name__}" on {http_string}')
            api.create_user(service.__name__, password)
            api.create_user_permission(service.__name__, pipeline.__name__)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{stub.__name__}" to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=stub.__name__)

