FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "flash-text.py", "--yaml_path", "flash-text.yml"]