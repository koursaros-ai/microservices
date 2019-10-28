FROM pytorch/pytorch:1.3-cuda10.1-cudnn7-runtime

RUN pip install grpcio pyzmq protobuf ruamel.yaml ruamel.yaml.clib aiohttp
RUN pip install git+https://github.com/colethienes/gnes.git --no-cache-dir --compile

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]