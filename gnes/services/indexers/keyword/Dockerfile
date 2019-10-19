FROM gnes/gnes:latest-alpine

RUN pip install pyahocorasick

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "aho-corasick.py", "--yaml_path", "aho-corasick.yml"]