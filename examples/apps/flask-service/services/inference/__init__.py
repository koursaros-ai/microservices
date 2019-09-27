from koursaros import Service
import os
import sys
print('starting inference...')
sys.path.append(os.getcwd())

# from koursaros.utils.bucket import download_and_unzip
from utils.model import Roberta

CHECKPOINT_FILE = 'checkpoint_best.pt'
NAME = 'fever'
CLASSES = ['NEI', 'REFUTES', 'SUPPORTS']

BATCH_SIZE = 4
MODELS_DIR = f'./'  # where to score the model locally
BUCKET = 'poloma-models'

# MODEL = f'{NAME}-model.tar.gz'  # bucket storage
# model_dir = MODELS_DIR + f'{NAME}-output/'
# if not os.path.isfile(model_dir + CHECKPOINT_FILE):
#     download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)

model = Roberta(
    MODELS_DIR + f'{NAME}-output/',
    CHECKPOINT_FILE,
    classes = CLASSES,
    force_gpu=False
)

service = Service(__file__)

@service.stub
def inference(claim_with_lines, publish):
    claim_text = claim_with_lines.claim.text
    evidence = claim_with_lines.lines[0].text

    label = model.classify(claim_text, evidence, probs=False)

    evaluated_claim = service.messages.EvaluatedClaim(
        claim = claim_with_lines.claim,
        evidence = claim_with_lines.lines,
        label = label
    )
    publish(evaluated_claim)