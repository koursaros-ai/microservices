FROM gnes/gnes:latest-alpine

RUN apk update
RUN apk add git
RUN pip uninstall gnes -y
RUN pip install aiohttp git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]