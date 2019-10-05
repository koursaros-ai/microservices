from koursaros.pipelines import factchecking
import sys
import os
import time
from ...utils.model import Roberta
from ...utils.buffer import batch_fn

regression_model = None
BATCH_SIZE = 8
CHECKPOINT_FILE = 'checkpoint_best.pt'
NAME = 'scorer'
MODELS_DIR = f'./flask-service/models/'  # where to score the model locally
# MODEL = f'{NAME}-model.tar.gz'  # bucket storage
# BATCH_SIZE = 4
# BUCKET = 'poloma-models'
# model_dir = MODELS_DIR + f'{NAME}-output/'
# if not os.path.isfile(model_dir + CHECKPOINT_FILE):
#     print('downloading model...')
#     download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)

pipeline = factchecking(__file__)
scorer = pipeline.services.scorer
inference = pipeline.services.inference


def load_model():
    global regression_model

    print('loading model')
    print(os.getcwd())

    regression_model = Roberta(
        MODELS_DIR + f'{NAME}-output/',
        CHECKPOINT_FILE,
        force_gpu=False
    )
    print('model loaded...')


@scorer.stubs.rerank
def rerank(claim_with_lines):
    print('ranking')

    def score(lines):
        claims = [claim_with_lines.claim.text] * len(lines)
        return regression_model.classify(claims, lines)

    results = []
    for scores, inputs in batch_fn(BATCH_SIZE, score, claim_with_lines.lines):
        for score, line in zip(scores, inputs):
            results.append((score, line))
    results.sort(key=lambda x: x[0], reverse=True)
    print("publishing")

    inference.stubs.label(inference.stubs.label.ClaimWithLines(
        claim=claim_with_lines.claim,
        lines=[el[1] for el in results[:5]]
    ))


if __name__ == "__main__":
    load_model()
    scorer.run()