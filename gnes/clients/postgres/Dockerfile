FROM gnes/gnes:latest-alpine

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev git
RUN pip install psycopg2 git+https://git@github.com/koursaros-ai/koursaros.git

ADD *.py *.yml ./

ENTRYPOINT ["python", "postgres.py", "--grpc_port", "5566"]