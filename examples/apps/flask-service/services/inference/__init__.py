from koursaros import Service
import sys
import os
import time
import threading
from ...utils.model import Roberta

from ...utils.buffer import batch_fn
# from utils.bucket import download_and_unzip

model = None
BATCH_SIZE = 4

def load_model():
    global model
    CHECKPOINT_FILE = 'checkpoint_best.pt'
    NAME = 'fever'
    CLASSES = ['NOT ENOUGH INFO', 'REFUTES', 'SUPPORTS']

    MODELS_DIR = f'./flask-service/models/' # where to score the model locally

    # BUCKET = 'poloma-models'
    # MODEL = f'{NAME}-model.tar.gz'  # bucket storage
    # model_dir = MODELS_DIR + f'{NAME}-output/'
    # if not os.path.isfile(model_dir + CHECKPOINT_FILE):
    #     download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)

    model = Roberta(
        MODELS_DIR + f'{NAME}-output/',
        CHECKPOINT_FILE,
        classes=CLASSES,
        force_gpu=False
    )

service = Service(__file__)

@service.stub
def inference(claim_with_lines, publish):
    claim_text = claim_with_lines.claim.text
    evidence = claim_with_lines.lines[0]

    label = model.classify([claim_text], [evidence], probs=False)[0]

    evaluated_claim = service.messages.EvaluatedClaim(
        claim = claim_with_lines.claim,
        evidence = claim_with_lines.lines,
        label = label
    )
    publish(evaluated_claim)

def main():
    print('running main inference')

    threads = service.run()
    load_model()
    for t in threads:
        t.start()

    for t in threads:
        t.join()
