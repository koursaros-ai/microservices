from koursaros import Service
from messages_pb2 import Notification
import os

service = Service(os.getcwd())


@service.pubber
def send(publish):
    publish(Notification())


@service.subber
def receive(notification, publish):
    print('Got notification!')


@service.main
def main(connection):
    if connection == 'dev_local':
        pass