FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "preprocess", "--yaml_path", "word-split.yml", "--py_path", "word-split.py"]