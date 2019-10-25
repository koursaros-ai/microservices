FROM pytorch/pytorch:1.1.0-cuda10.0-cudnn7.5-runtime

RUN pip install grpcio pyzmq protobuf ruamel.yaml ruamel.yaml.clib aiohttp
RUN echo 7
RUN pip install git+https://github.com/colethienes/gnes.git --no-cache-dir --compile

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]