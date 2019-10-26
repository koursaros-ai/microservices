FROM gnes/gnes:latest-buster

RUN apt-get install python-virtualenv python-dev librocksdb-dev
RUN pip install python-rocksdb

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index"]