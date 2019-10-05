from koursaros.pipelines import factchecking
import sys
import os
import time
from threading import Thread
from ...utils.model import Roberta

from ...utils.buffer import batch_fn

# from utils.bucket import download_and_unzip

model = None
BATCH_SIZE = 4
CHECKPOINT_FILE = 'checkpoint_best.pt'
NAME = 'fever'
CLASSES = ['NOT ENOUGH INFO', 'REFUTES', 'SUPPORTS']
MODELS_DIR = f'./flask-service/models/'  # where to score the model locally


pipeline = factchecking(__file__)
inference = pipeline.services.inference
backend = pipeline.services.backend


def load_model():
    global model

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


@inference.stubs.label
def inference(claim_with_lines, publish):
    claim_text = claim_with_lines.claim.text
    evidence = claim_with_lines.lines[0]

    label = model.classify([claim_text], [evidence], probs=False)[0]

    evaluated_claim = inference.stubs.label.EvaluatedClaim(
        claim=claim_with_lines.claim,
        evidence=claim_with_lines.lines,
        label=label
    )
    backend.stubs.receive(evaluated_claim)


if __name__ == "__main__":
    print('running main inference')

    t = Thread(target=inference.run)
    t.start()
    load_model()

    t.join()
