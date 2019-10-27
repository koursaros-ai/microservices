FROM gnes/gnes:latest-alpine

RUN pip install whoosh
RUN apt-get update
RUN apt-get install -y python-dev librocksdb-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libgflags-dev
RUN pip install python-rocksdb --no-cache-dir --compile

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "whoosh.py"]