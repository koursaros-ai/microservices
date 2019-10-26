FROM gnes/gnes:latest-buster

RUN apt-get update
RUN apt-get install -y python-virtualenv python-dev librocksdb-dev build-essential libsnappy-dev zlib1g-dev libbz2-dev libgflags-dev
RUN pip install python-rocksdb --no-cache-dir --compile

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index"]