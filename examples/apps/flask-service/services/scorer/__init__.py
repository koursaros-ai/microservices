from koursaros import Service


regression_model = None

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
        lines=["test", "test"]#[el[1] for el in results[:5]]
    ))


def main():
    threads = service.run()

    print('loading model')
    global regression_model

    from fairseq.models.roberta import RobertaModel
    from fairseq.data.data_utils import collate_tokens

    class Roberta:

        def __init__(self, model_dir, ckpt_file, classes=None, force_gpu=False):
            self.model = RobertaModel.from_pretrained(model_dir, checkpoint_file=ckpt_file)
            self.model.eval()  # disable dropout
            self.classes = classes
            if force_gpu:
                self.model.cuda()
            else:
                try:
                    self.model.cuda()
                except AssertionError as ae:
                    print(f'{ae}\n\nNot using GPU...')

        def classify(self, *args, probs=False):

            if self.classes is None:
                batch = collate_tokens([self.model.encode(*arg) for arg in zip(*args)], pad_idx=1)
                labels = self.model.predict('sentence_classification_head', batch, return_logits=True).tolist()
                labels = [l[0] for l in labels]
                return labels

            roberta = self.model
            batch = collate_tokens([roberta.encode(*arg) for arg in zip(*args)], pad_idx=1)
            labels = roberta.predict('sentence_classification_head', batch)
            if not probs:
                return [self.classes[label] for label in labels.argmax(dim=1)]
            else:
                return labels.tolist()

        def trim_sentence(self, sent, max_len):
            return sent if len(sent) < max_len else sent[:max_len]

        def encode(self, sentences, pooling_strategy='cls', layer=-4, max_len=400):
            roberta = self.model
            batch = collate_tokens([self.trim_sentence(roberta.encode(sentence), max_len)
                                    for sentence in sentences], pad_idx=1)
            features = roberta.extract_features(batch, return_all_hiddens=True)[layer]
            if pooling_strategy == 'cls':
                return features[:, 0]
            elif pooling_strategy == 'mean':
                return features.mean(dim=1)
            elif pooling_strategy == 'max':
                return features.max(dim=1)[0]
            else:
                raise NotImplementedError()

    CHECKPOINT_FILE = 'checkpoint_best.pt'
    NAME = 'scorer'
    MODELS_DIR = f'./'  # where to score the model locally

    MODEL = f'{NAME}-model.tar.gz'  # bucket storage
    BATCH_SIZE = 4
    BUCKET = 'poloma-models'
    model_dir = MODELS_DIR + f'{NAME}-output/'
    # if not os.path.isfile(model_dir + CHECKPOINT_FILE):
    #     print('downloading model...')
    #     download_and_unzip(BUCKET, MODEL, MODELS_DIR, archive=True)

    print('building model')

    regression_model= Roberta(
        MODELS_DIR + f'{NAME}-output/',
        CHECKPOINT_FILE,
        force_gpu=False
    )

    for t in threads:
        t.start()

    for t in threads:
        t.join()
        print('exiting scorer')