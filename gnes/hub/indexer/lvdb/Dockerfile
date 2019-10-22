FROM gnes/gnes:latest-buster

RUN pip install plyvel>=1.0.5 --no-cache-dir --compile

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index"]