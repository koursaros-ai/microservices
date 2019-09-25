from koursaros import Service
from ..messages import Number

service = Service(__name__)


@service.pubber
def send(publish):
    for i in range(100):
        print(f'Please factor {i}!')
        number = Number(number=i)
        publish(number)


@service.subber
def receive(factors, publish):
    print(f'I got factors {factors.factors} for {factors.number}')


@service.main
def main(connection):
    if connection == 'dev_local':
        print('Connected locally!')