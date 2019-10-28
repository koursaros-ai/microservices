FROM gnes/gnes:latest-buster

RUN apt-get update
RUN apt-get install git
RUN pip install grpcio pyzmq protobuf ruamel.yaml ruamel.yaml.clib aiohttp
RUN pip install git+https://github.com/colethienes/gnes.git --no-cache-dir --compile

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]