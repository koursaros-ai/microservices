FROM python:3.7.4-alpine AS base

RUN apk add --no-cache \
            --virtual=.build-dependencies \
            build-base g++ gfortran file binutils zeromq-dev \
            musl-dev python3-dev py-pgen cython openblas-dev && \
    apk add --no-cache libstdc++ openblas libzmq
RUN apk add git
RUN pip install aiohttp git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]