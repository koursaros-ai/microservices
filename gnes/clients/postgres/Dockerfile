FROM gnes/gnes:latest-alpine

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install psycopg2


ENTRYPOINT ["python", "postgres.py", "--grpc_port", "5566"]