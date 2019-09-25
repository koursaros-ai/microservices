from koursaros import Service
from ..models.factorer import Factorer
from ..messages import Factors

service = Service(__name__)

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