FROM gnes/gnes:latest-buster

RUN pip install plyvel>=1.0.5 --no-cache-dir --compile
RUN pip uninstall gnes -y
RUN apt update
RUN apt install git -y
RUN echo 5
RUN pip install git+https://git@github.com/colethienes/gnes.git

ADD *.yml ./

ENTRYPOINT ["gnes", "index", "--yaml_path", "lvdb.yml"]