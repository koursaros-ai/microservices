FROM gnes/gnes:latest-alpine

# placeholder to force rebuild
RUN echo 3

ADD *.py *.yml ./
RUN apk add git
RUN pip install git+https://git@github.com/koursaros-ai/koursaros.git

ENTRYPOINT ["gnes", "preprocess", "--yaml_path", "word-split.yml"]