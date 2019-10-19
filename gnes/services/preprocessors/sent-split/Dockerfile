FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "preprocess", "--yaml_path", "json-mode.yml"]