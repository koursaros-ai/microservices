FROM gnes/gnes:latest-buster

RUN echo 'yo'

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "simple_dict.py"]