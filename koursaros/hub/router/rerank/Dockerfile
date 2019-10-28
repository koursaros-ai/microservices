FROM pytorch/pytorch

RUN pip install -U transformers gnes --no-cache-dir --compile

RUN mkdir -p /workspace
WORKDIR /workspace

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "route", "--py_path", "rerank.py"]