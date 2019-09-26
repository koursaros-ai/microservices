from koursaros import Service


service = Service(__file__)


@service.pubber
def send(publish):
    notification = service.messages.Notification()
    publish(notification)


@service.subber
def receive(notification, publish):
    print('Got notification!')


@service.main
def main(connection):
    if connection == 'dev_local':
        pass