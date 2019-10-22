FROM gnes/gnes:latest-buster

RUN apt update
RUN apt install libpq-dev gcc python3-dev musl-dev git -y
RUN pip install psycopg2 git+https://git@github.com/koursaros-ai/koursaros.git

ADD *.py *.yml ./

ENTRYPOINT ["python", "postgres.py", "--start_doc_id", "1"]