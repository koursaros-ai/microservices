FROM pytorch/pytorch

RUN pip install -U transformers gnes --no-cache-dir --compile && echo 'yo'

ADD *.py *.yml ./

ENTRYPOINT ["gnes", "route", "--py_path", "rerank.py"]