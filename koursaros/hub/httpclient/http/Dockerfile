FROM gnes/gnes:latest-alpine

RUN apk add git
RUN pip uninstall gnes -y
RUN pip install git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]