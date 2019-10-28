FROM pytorch/pytorch

RUN pip install -U transformers gnes --no-cache-dir --compile

ADD *.py *.yml ./
RUN pwd && echo 'yo'

ENTRYPOINT ["pwd"] # "gnes", "route", "--py_path", "rerank.py