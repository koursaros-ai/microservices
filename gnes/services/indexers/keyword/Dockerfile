FROM gnes/gnes:latest-alpine

RUN apk add gcc
RUN pip install pyahocorasick

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "keyword.py"]