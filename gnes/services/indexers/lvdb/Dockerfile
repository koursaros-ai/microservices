FROM gnes/gnes:latest-alpine

ADD *.yml ./

ENTRYPOINT ["gnes", "index", "--yaml_path", "lvdb.yml"]