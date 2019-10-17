FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./
RUN pip install git+https://git@github.com/koursaros-ai/koursaros.git

ENTRYPOINT ["gnes", "preprocess", "--yaml_path", "word-split.yml"]