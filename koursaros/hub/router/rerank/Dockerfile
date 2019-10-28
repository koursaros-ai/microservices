FROM pytorch/pytorch:1.3-cuda10.1-cudnn7-runtime

RUN pip install -U transformers gnes --no-cache-dir --compile

WORKDIR /
ADD *.py *.yml ./

ENTRYPOINT ["gnes", "route", "--py_path", "rerank.py"]