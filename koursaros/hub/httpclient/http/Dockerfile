FROM gnes/gnes:latest-ubuntu

RUN apt-get install git
RUN pip uninstall gnes -y
RUN pip install git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]