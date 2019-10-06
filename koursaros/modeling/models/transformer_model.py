from ..model import Model
import torch.nn, torch.tensor
from transformers import *

MODEL_CLASSES = {
    'bert': (BertConfig, BertForSequenceClassification, BertTokenizer),
    'xlnet': (XLNetConfig, XLNetForSequenceClassification, XLNetTokenizer),
    'xlm': (XLMConfig, XLMForSequenceClassification, XLMTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForSequenceClassification, DistilBertTokenizer)
}

class TransformerModel (Model):

     def __init__(self, *args):
         super().__init__(*args)
         if self.config.task == 'classification':
            config, model, tokenizer = MODEL_CLASSES[self.config.base]
         else:
            raise NotImplementedError()

         self.model = model.from_pretrained(self.checkpoint)
         self.tokenizer = tokenizer.from_pretrained(self.checkpoint)

     def extract_features(self, data):
         return [self.tokenizer.encode(b) for b in data]

     def train(self):
         ### In Transformers, optimizer and schedules are splitted and instantiated like this:
         train_data, test_data = self.get_data()
         batch_size = 4
         max_grad_norm = 1.0
         optimizer = AdamW(self.model.parameters(), lr=float(self.config.training.learning_rate),
                           correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
         num_warmup_steps = int(0.06 * len(train_data))
         scheduler = WarmupLinearSchedule(optimizer, warmup_steps=num_warmup_steps,
                                          t_total=(self.config.training.epochs * len(train_data) / batch_size))
         self.model.train()

         for epoch in range(0, self.config.training.epochs):
             ### and used like this:
             for i, batch in enumerate(train_data):
                 features = torch.tensor(self.extract_features(batch))
                 outputs = self.model(features)
                 loss = outputs[0]
                 loss.backward()
                 torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_grad_norm)
                 optimizer.step()
                 print(f'step {i}')
                 scheduler.step(epoch=epoch)
                 optimizer.zero_grad()

     def eval(self):
         pass

     def run(self, *args):
         # Protobuffs in and protobuffs out
         batch = self.tokenizer(args[0], args[1])
         return self.model(batch)

     @staticmethod
     def architectures():
         return list(MODEL_CLASSES.keys())