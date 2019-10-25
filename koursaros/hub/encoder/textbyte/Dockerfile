FROM gnes/gnes:latest-alpine

ADD *.py *.yml ./

RUN echo 'yo'

ENTRYPOINT ["gnes", "encode", "--py_path", "textbyte.py"]