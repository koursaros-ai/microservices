FROM python:3.7.4-alpine AS base

RUN apt install git -y
RUN pip install aiohttp git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]