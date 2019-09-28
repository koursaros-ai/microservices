

def bind_rabbitmq(app, args):

    from ...utils import BOLD
    from .api import AdminAPI
    import requests
    import pika

    connection = app.connections[args.connection]

    host = connection.host
    http_port = connection.http_port
    port = connection.port
    username = connection.username
    password = connection.password

    url = f'http://{host}:{http_port}'
    ip = f'{host}:{port}'

    api = AdminAPI(url=url, auth=(username, password))  # admin connection

    for pipeline in args.pipeline:
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

        for stub in app.pipelines[pipeline].stubs.values():
            queue = stub.service + '.' + stub.name
            print(f'Creating user "{pipeline}" on {http_string}')
            api.create_user(stub.service, password)
            api.create_user_permission(stub.service, pipeline)

            print(f'Creating queue "{queue}" on {pika_string}')
            channel.queue_declare(queue=queue, durable=True)

            print(f'Binding "{stub.name}" to "{queue}" queue on {pika_string}')
            channel.queue_bind(exchange='nyse', queue=queue, routing_key=stub.name)

