FROM gnes/gnes:latest-alpine

RUN pip install aiohttp

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "client", "http"]