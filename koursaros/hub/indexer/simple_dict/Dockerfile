FROM gnes/gnes:latest-buster

RUN apt-get update
RUN apt-get install -y git
RUN pip install grpcio pyzmq protobuf ruamel.yaml ruamel.yaml.clib aiohttp
RUN pip install --upgrade git+https://github.com/colethienes/gnes.git --no-cache-dir --compile

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "index", "--py_path", "simple_dict.py"]