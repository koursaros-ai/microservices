class Roberta:

    def __init__(self, fairseq, model_dir, ckpt_file, classes=None, force_gpu=False):
        self.model = fairseq.models.roberta.RobertaModel.from_pretrained(model_dir, checkpoint_file=ckpt_file)
        self.collate_tokens = fairseq.data.data_utils.collate_tokens
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
            batch = self.collate_tokens([self.model.encode(*arg) for arg in zip(*args)], pad_idx=1)
            labels = self.model.predict('sentence_classification_head', batch, return_logits=True).tolist()
            labels = [l[0] for l in labels]
            return labels

        roberta = self.model
        batch = self.collate_tokens([roberta.encode(*arg) for arg in zip(*args)], pad_idx=1)
        labels = roberta.predict('sentence_classification_head', batch)
        if not probs:
            return [self.classes[label] for label in labels.argmax(dim=1)]
        else:
            return labels.tolist()

    def trim_sentence(self, sent, max_len):
        return sent if len(sent) < max_len else sent[:max_len]

    def encode(self, sentences, pooling_strategy='cls', layer=-4, max_len=400):
        roberta = self.model
        batch = self.collate_tokens([self.trim_sentence(roberta.encode(sentence), max_len)
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
