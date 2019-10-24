FROM python:3.7.4-alpine AS base

RUN apk update
RUN apk add git
RUN pip install aiohttp git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]