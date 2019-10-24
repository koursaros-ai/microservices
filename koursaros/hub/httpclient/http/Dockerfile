FROM gnes/gnes:latest-alpine

RUN apk add git
RUN pip install numpy
RUN pip install grpcio
RUN pip install aiohttp
RUN pip install git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]