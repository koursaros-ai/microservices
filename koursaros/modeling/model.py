import os
from koursaros.utils.database.psql import Conn
from koursaros.utils.misc import gb_free_space
from koursaros.utils.bucket import bucket_contains, download_and_unzip
from kctl.logger import set_logger
from .data import *

logger = set_logger('MODELS')

class Model(object):

    def __init__(self, config, training):
        if gb_free_space() < 3:
            logger.error("There is not enough space on your disk, please allocate more!")
            raise SystemError

        self.config = config
        self.version = config.hash
        self.dir = '.model-data'

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self.ckpt_dir = f'{self.dir}/{self.version}/'
        logger.info("Local model cache dir %s" %self.ckpt_dir)
        if not 'training' in self.config: # use a default model
            logger.info('Loading model from default checkpoint')
            self.checkpoint = self.config.checkpoint
            self.trained = True
        elif os.path.exists(self.ckpt_dir + 'config.json') and not training: # model already trained
            logger.info('Loading trained model')
            self.checkpoint = self.ckpt_dir
            self.trained = True
        elif bucket_contains(f'{self.version}.tar.gz'):
            logger.info(f'Downloading and extracting from bucket {self.config.repo}')
            download_and_unzip(self.config.repo.split('//')[-1],
                               f'{self.version}.tar.gz', self.dir)
            self.checkpoint = self.ckpt_dir
            assert(os.path.exists(self.ckpt_dir + 'config.json'))
            self.trained = True
        else: # init model for training
            logger.info('Initializing model for training')
            if not training:
                logger.error('Please train model before deploying')
                raise SystemError
            self.data_dir = os.path.join(self.dir, self.version)
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            if not os.path.exists(self.ckpt_dir):
                os.makedirs(self.ckpt_dir)
            self.checkpoint = config.training.checkpoint
            self.trained = False

    def get_data(self):
        """
        Get training data based on yaml config and connection
        :return:
        """
        data = self.config.training.data
        if data.source == 'postgres':
            p = Conn()
            query_fn = p.query
            return query_fn(select_all(data.schema, data.train)), \
                   query_fn(select_all(data.schema, data.test))
        else:
            return get_rows_from_tsv(data.train), get_rows_from_tsv(data.test)

    def train(self):
        """
        Runs training as defined in the model yaml. Saves model to directory
        .cache/<md5 hash of yaml>
        :return: evaluation metric
        """
        raise NotImplementedError()

    def run(self, *args):
        """
        Runs inference on arbitrary args
        :param args: sent_a, sent_b for classification / regression task.
        :return:
        """
        raise NotImplementedError()

    def save_model(self):
        # append hash of yaml to model checkpoint
        raise NotImplementedError()

    @staticmethod
    def architectures():
        raise NotImplementedError()

    def getInputProto(self):
        raise NotImplementedError()

    def getOutputProto(self):
        raise NotImplementedError()

