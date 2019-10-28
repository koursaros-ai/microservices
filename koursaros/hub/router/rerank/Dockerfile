FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-devel


RUN pip install -U transformers gnes --no-cache-dir --compile

WORKDIR /
ADD *.py *.yml ./
RUN nvidia-smi

ENTRYPOINT ["gnes", "route", "--py_path", "rerank.py"]