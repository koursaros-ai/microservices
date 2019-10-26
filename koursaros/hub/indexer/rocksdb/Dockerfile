FROM gnes/gnes:latest-buster

RUN apt-get update
RUN apt-get install -f python-virtualenv python-dev librocksdb-dev
RUN pip install python-rocksdb

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index"]