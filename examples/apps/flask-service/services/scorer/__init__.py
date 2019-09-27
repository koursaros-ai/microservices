from koursaros import Service
import sys
import os
import time
import threading

# from utils.buffer import batch_fn
# from utils.bucket import download_and_unzip


def load_model():
    print('appending to sys path')
    print('importing fairseq / roberta')
    import numpy as np
    # from fairseq.models.roberta import RobertaModel
    # from fairseq.data.data_utils import collate_tokens
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')
    print('IMPORTED FAIRSEQ')

    #
    # # from utils.model import Roberta
    # print('loading model')
    # CHECKPOINT_FILE = 'checkpoint_best.pt'
    # NAME = 'scorer'
    # MODELS_DIR = f'./'  # where to score the model locally
    #
    # MODEL = f'{NAME}-model.tar.gz'  # bucket storage
    # BATCH_SIZE = 4
    # BUCKET = 'poloma-models'
    # model_dir = MODELS_DIR + f'{NAME}-output/'
    # # if not os.path.isfile(model_dir + CHECKPOINT_FILE):
    # #     print('downloading model...')
    # #     download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)
    # print('loading model')
    #
    # regression_model = Roberta(
    #     MODELS_DIR + f'{NAME}-output/',
    #     CHECKPOINT_FILE,
    #     force_gpu=False
    # )


service = Service(__file__)

@service.stub
def rerank(claim_with_lines, publish):
    # print('ranking')
    # def score(lines):
    #     claims = [claim_with_lines.claim.text] * len(lines)
    #     return regression_model.classify(claims, lines)
    #
    # results = []
    # for scores, inputs in batch_fn(BATCH_SIZE, score, claim_with_lines.lines):
    #     for score, line in zip(scores, inputs):
    #         results.append((score, line))
    # results.sort(key=lambda x: x[0], reverse=True)
    print("publishing")
    publish(service.messages.ClaimWithLines(
        claim=claim_with_lines.claim,
        lines=["test", "test"] #[el[1] for el in results[:5]]
    ))

def fake_load():
    for i in range(0, 5):
        time.sleep(1)
        print('hi!!!!')

def main():
    print('running main scorer')
    load_model_thread = threading.Thread(
        target=load_model
    )

    threads = service.run()
    threads.append(load_model_thread)

    for t in threads:
        print('starting thread scorer')
        t.start()

    for t in threads:
        print('waiting to join thread scorer')
        t.join()
    print('scorer thread exited')