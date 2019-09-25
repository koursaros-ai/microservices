from koursaros import Service
from functools import reduce
from ..messages import Factors

service = Service(__name__)


class Factorer:
    @staticmethod
    def factor(n):
        return set(reduce(
            list.__add__,
            ([i, n // i] for i in range(1, int(n ** 0.5) + 1))
        ))


model = Factorer()


@service.subber
def factor(number, publish):
    num = number.number
    print(f'Processing {num}')
    factors = model.factor(num)
    publish(Factors(
        number=num,
        factors=factors
    ))


@service.main
def main(connection):
    if connection == 'dev_local':
        print('Connected locally!')