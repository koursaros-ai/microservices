from .model import Model
import torch.nn
from transformers import *

MODEL_CLASSES = {
    'bert': (BertConfig, BertForSequenceClassification, BertTokenizer),
    'xlnet': (XLNetConfig, XLNetForSequenceClassification, XLNetTokenizer),
    'xlm': (XLMConfig, XLMForSequenceClassification, XLMTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForSequenceClassification, DistilBertTokenizer)
}

class TransformerModel (Model):

     def __init__(self):
         super().__init__()
         if self.task == 'classification':
            config, model, tokenizer = MODEL_CLASSES[self.architecture]
         else:
            pass
         self.model = model.from_pretrained()
         self.tokenizer = tokenizer.from_pretrained()


     def train(self):
         ### In Transformers, optimizer and schedules are splitted and instantiated like this:
         optimizer = AdamW(self.model.parameters(), lr=self.lr,
                           correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
         scheduler = WarmupLinearSchedule(optimizer, warmup_steps=num_warmup_steps,
                                          t_total=num_total_steps)  # PyTorch scheduler
         ### and used like this:
         for batch in train_data:
             loss = model(batch)
             loss.backward()
             torch.nn.utils.clip_grad_norm_(model.parameters(),
                                            max_grad_norm)  # Gradient clipping is not in AdamW anymore (so you can use amp without issue)
             optimizer.step()
             scheduler.step()
             optimizer.zero_grad()

     def run(self, *args):
         pass