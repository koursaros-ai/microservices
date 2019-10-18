FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "encode", "--py_path", "text-byte.py", "--yaml_path", "text-byte.yml"]