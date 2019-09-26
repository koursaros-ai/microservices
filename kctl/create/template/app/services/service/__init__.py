from koursaros import Service
from messages_pb2 import Notification

service = Service(__name__)


@service.pubber
def send(publish):
    pass


@service.subber
def receive(notification, publish):
    pass


@service.main
def main(connection):
    if connection == 'dev_local':
        pass