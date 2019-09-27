from koursaros import Service
import os
import sys
print('starting inference...')
sys.path.append(os.getcwd())

from koursaros.utils.bucket import download_and_unzip
from koursaros.utils.model import Roberta
from koursaros.constants import GOOGLE_CREDENTIALS_PATH
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS_PATH
CHECKPOINT_FILE = 'checkpoint_last.pt'
NAME = 'fever'
CLASSES = ['NEI', 'REFUTES', 'SUPPORTS']

BATCH_SIZE = 4
MODELS_DIR = f'./'  # where to score the model locally
BUCKET = 'poloma-models'

MODEL = f'{NAME}-model.tar.gz'  # bucket storage
model_dir = MODELS_DIR + f'{NAME}-output/'
if not os.path.isfile(model_dir + CHECKPOINT_FILE):
    download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)

model = Roberta(
    MODELS_DIR + f'{NAME}-output/',
    CHECKPOINT_FILE,
    classes = CLASSES,
    force_gpu=False
)