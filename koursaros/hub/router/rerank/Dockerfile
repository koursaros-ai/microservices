FROM pytorch/pytorch

RUN pip install -U transformers gnes --no-cache-dir --compile

ADD *.py *.yml ./

WORKDIR ./
ENTRYPOINT ["gnes", "route", "--py_path", "rerank.py"]