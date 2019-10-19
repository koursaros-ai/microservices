FROM gnes/gnes:latest-buster

RUN apt update
RUN apt install libpq-dev gcc python3-dev musl-dev git -y
RUN pip install psycopg2 git+https://git@github.com/koursaros-ai/koursaros.git
RUN pip uninstall gnes -y
RUN echo 2
RUN pip install git+https://git@github.com/colethienes/gnes.git

ADD *.py *.yml ./

ENTRYPOINT ["python", "postgres.py", "--grpc_port", "8800"]