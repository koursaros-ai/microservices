FROM gnes/gnes:latest-buster

RUN pip install whoosh

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "whoosh.py"]