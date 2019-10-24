FROM ubuntu:18.04 AS base

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
 && locale-gen "en_US.UTF-8"

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential python3-dev python3-pip python3-setuptools libopenblas-dev && \
    export LC_ALL=en_US.UTF-8 && export LANG=en_US.UTF-8 && export LC_CTYPE=en_US.UTF-8 && \
    ln -s /usr/bin/python3 python && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ADD setup.py MANIFEST.in requirements.txt README.md ./
ADD gnes ./gnes/

RUN apt-get install git
RUN pip uninstall gnes -y
RUN pip install git+https://github.com/colethienes/gnes

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]