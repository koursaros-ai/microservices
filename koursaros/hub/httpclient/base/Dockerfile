FROM gnes/gnes:latest-alpine

RUN pip install aiohttp

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]