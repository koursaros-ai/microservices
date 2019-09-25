INIT_TEMPLATE = '''from ..base import Microservice

{setup}

################
# Microservice #
################

microservice = Microservice(__name__)

{pubber}

@microservice.subber
{subber}

@microservice.main
{main}

'''

HELLO_SETUP = 'SEND_SUP = False'

HELLO_MAIN = '''
def main(connection):
    global SEND_SUP
    if connection == 'dev_local':
        SEND_SUP = True
'''

HELLO_PUBBER = '''
@microservice.pubber
def send_hello(publish):
    if SEND_SUP:
        proto = 'sup'
        publish(proto)
'''

HELLO_SUBBER = '''
def respond_to_hello(proto, publish):
    print('Received', proto)
    new_proto = 'hello there from the {service}!'
    publish(new_proto)
'''

HELLO_TEMPLATE = INIT_TEMPLATE.format(
    setup=HELLO_SETUP,
    pubber=HELLO_PUBBER,
    subber=HELLO_SUBBER,
    main=HELLO_MAIN
)

MODEL_SETUP = '''
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

log.info('initializing {microservice}...')
from ...utils.bucket import download_and_unzip
from ...utils.model import Roberta
from ...utils.buffer import batch_fn
from ...constants import GOOGLE_CREDENTIALS_PATH
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS_PATH
CHECKPOINT_FILE = 'checkpoint_best.pt'
NAME = '{microservice}'
MODELS_DIR = {models_dir}  # where to score the model locally
MODEL = NAME + '-model.tar.gz'  # bucket storage
BATCH_SIZE = 4 # default for modern GPU
BUCKET = {bucket}
model_dir = MODELS_DIR + NAME + '-output/'

if not os.path.isfile(model_dir + CHECKPOINT_FILE):
    download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)
'''

INFERENCE_SETUP = '''
CLASSES = {classes}
model = Roberta(
    model_dir,
    CHECKPOINT_FILE,
    classes=CLASSES,
    force_gpu=True
)'''

REGRESSION_SETUP = '''
model = Roberta(
    model_dir,
    CHECKPOINT_FILE,
    force_gpu=True
)
'''

RERANK_SUBBER = '''
@microservice.subber
def rank(claim_with_lines: ClaimWithLines, publish):
    claim_text = claim_with_lines.claim.text

    def model_fn(batch):
        evidences = [l.text for l in batch]
        claims = [claim_text] * len(evidences)
        return model.classify(claims, evidences, probs=True)

    ranked_lines = []
    for labels, lines in batch_fn(BATCH_SIZE, model_fn, claim_with_lines.lines):
        for label, line in zip(labels, lines):
            ranked_lines.append((label[1], line))

    ranked_lines.sort(key=lambda x: x[0], reverse=True)
    topk = [line[1] for line in ranked_lines][:15]

    claim_with_lines = ClaimWithLines(
        claim=claim_with_lines.claim,
        lines=topk
    )
    log.info("sending scored claim")
    publish(claim_with_lines)
'''

INFERENCE_SUBBER = '''
@microservice.subber
def inference(sample: Sample, publish):
    claim_text = claim_with_lines.claim.text

    def model_fn(batch):
        evidences = [l.text for l in batch]
        claims = [claim_text] * len(evidences)
        results = model.classify(claims, evidences, probs=False)
        return results

    evidence = dict()
    for label in CLASSES:
        evidence[label] = []

    for labels, lines in batch_fn(BATCH_SIZE, model_fn, claim_with_lines.lines):
        for label, line in zip(labels, lines):
            evidence[label].append(line)

    sorted_evidence = list(evidence.items())
    sorted_evidence.sort(key=lambda x: len(x[1]), reverse=True)
    label = sorted_evidence[0][0]

    evaluated_claim = EvaluatedClaim(
        claim = ClaimWithLines(
            claim=claim_with_lines.claim,
            lines=claim_with_lines.lines
        ),
        label = label
    )
    publish(evaluated_claim)
'''


SERVICE_TEMPLATE = '''
version: '3.7'

microservice:
  from: {registry}/{base_image}
  image: {registry}/{microservice}
  deps:
    - {dependencies}
  entrypoint: python -m koursaros.microservice.{microservice}
  replicas: 1
'''