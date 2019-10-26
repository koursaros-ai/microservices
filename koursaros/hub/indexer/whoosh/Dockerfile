FROM gnes/gnes:latest-alpine

RUN pip install whoosh

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "whoosh.py"]