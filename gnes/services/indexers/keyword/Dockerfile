FROM gnes/gnes:latest-alpine

RUN apk add gcc python3-dev musl-dev
RUN pip install pyahocorasick

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "keyword.py"]