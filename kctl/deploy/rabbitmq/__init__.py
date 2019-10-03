

def bind_rabbitmq(args):

    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    import koursaros.pipelines
    pipeline = getattr(koursaros.pipelines, args.pipeline_name)
    pipeline = pipeline(None)

    connection = pipeline.Connections.getactive()
    import pdb; pdb.set_trace()
    host = connection.host
    http_port = connection.http_port
    port = connection.port
    username = connection.username
    password = connection.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    pipeline_cls = pipeline.__class__.__name__
    http_string = f'vhost "{pipeline_cls}" on {BOLD.format(url)}'
    pika_string = f'vhost "{pipeline_cls}" on {BOLD.format(ip)}'

    try:
        print(f'Deleting {http_string}')
        api.delete_vhost(pipeline_cls)
    except requests.exceptions.HTTPError:
        print(f'Not found: {http_string}')

    print(f'Creating {http_string}')
    api.create_vhost(pipeline_cls)
    api.create_user_permission(username, pipeline_cls)

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, pipeline_cls, credentials)
    connection = pika.BlockingConnection(parameters=parameters)  # pika connection
    channel = connection.channel()

    print(f'Creating exchange "nyse" on {pika_string}')
    channel.exchange_declare(exchange='nyse', exchange_type='direct')

    for Service in pipeline.Services:
        for Stub in Service.Stubs:
            service_cls = Service.__class__.__name__
            stub_cls = Stub.__class__.__name__
            queue = service_cls + '.' + stub_cls
            print(f'Creating user "{service_cls}" on {http_string}')
            api.create_user(service_cls, password)
            api.create_user_permission(service_cls, pipeline_cls)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{stub_cls}" to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=queue)

