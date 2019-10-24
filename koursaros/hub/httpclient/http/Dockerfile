FROM pytorch/pytorch:1.1.0-cuda10.0-cudnn7.5-runtime

RUN pip install git+https://github.com/colethienes/gnes.git --no-cache-dir --compile
RUN pip install

COPY . ./workspace
WORKDIR /workspace

ENTRYPOINT ["gnes", "client", "http"]