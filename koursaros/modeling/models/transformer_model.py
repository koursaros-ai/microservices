from ..model import Model
import torch.nn, torch.tensor, torch.distributed
from transformers import *
from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,
                              TensorDataset, DistributedSampler)
from tensorboardX import SummaryWriter
from tqdm import tqdm, trange
import numpy as np
import os

MODEL_CLASSES = {
    'bert': (BertConfig, BertForSequenceClassification, BertTokenizer),
    'xlnet': (XLNetConfig, XLNetForSequenceClassification, XLNetTokenizer),
    'xlm': (XLMConfig, XLMForSequenceClassification, XLMTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForSequenceClassification, DistilBertTokenizer)
}


class TransformerModel(Model):

    def __init__(self, *args):
        super().__init__(*args)
        if self.config.task == 'classification' or self.config.task == 'regression':
            config, model, tokenizer = MODEL_CLASSES[self.config.base]
        else:
            raise NotImplementedError()

        self.model_config = config.from_pretrained(self.checkpoint)
        self.model_config.num_labels = len(self.config.labels)
        self.model = model.from_pretrained(self.checkpoint, config=self.model_config)
        self.tokenizer = tokenizer.from_pretrained(self.checkpoint)
        self.batch_size = 8
        self.max_grad_norm = 1.0
        self.weight_decay = 0.0
        self.n_gpu = 1
        self.local_rank = -1
        self.gradient_accumulation_steps = 1
        self.fp16 = True
        self.logging_steps = 1000
        self.save_steps = 1000
        self.max_length=512
        self.evaluate_during_training = True
        self.pad_token_segment_id = 4 if self.config.base == 'xlnet' else 0
        self.pad_on_left = True
        self.pad_token = 0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def extract_features(self, data):
        return [self.tokenizer.encode(*b[:2], add_special_tokens=True) for b in data]

    def train(self):
        ### In Transformers, optimizer and schedules are splitted and instantiated like this:

        tb_writer = SummaryWriter()

        train_dataset, test_dataset = self.get_data()
        train_dataset = self.load_and_cache_examples(train_dataset)
        epochs = int(self.config.training.epochs)
        optimizer = AdamW(self.model.parameters(), lr=float(self.config.training.learning_rate),
                          correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
        num_warmup_steps = int(0.06 * len(train_dataset))
        scheduler = WarmupLinearSchedule(optimizer, warmup_steps=num_warmup_steps,
                                         t_total=(self.config.training.epochs * len(train_dataset) / self.batch_size))

        train_sampler = RandomSampler(train_dataset)
        train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=self.batch_size)

        t_total = len(train_dataloader) // epochs

        # Prepare optimizer and schedule (linear warmup and decay)
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
             'weight_decay': self.weight_decay},
            {'params': [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)],
             'weight_decay': 0.0}
        ]
        if self.fp16:
            try:
                from apex import amp
            except ImportError:
                raise ImportError("Please install apex from https://www.github.com/nvidia/apex to use fp16 training.")
            model, optimizer = amp.initialize(self.model, optimizer)

        # # multi-gpu training (should be after apex fp16 initialization)
        # if self.n_gpu > 1:
        #     model = torch.nn.DataParallel(self.model)
        #
        # # Distributed training (should be after apex fp16 initialization)
        # if self.local_rank != -1:
        #     model = torch.nn.parallel.DistributedDataParallel(self.model, device_ids=[self.local_rank],
        #                                                       output_device=self.local_rank,
        #                                                       find_unused_parameters=True)

        # Train!
        print("***** Running training *****")
        print("  Num examples = ", len(train_dataset))
        print("  Num Epochs = ", epochs)
        print("  Total train batch size (w. parallel, distributed & accumulation) = ",
                    self.batch_size * (
                        torch.distributed.get_world_size() if self.local_rank != -1 else 1))
        print("  Total optimization steps = ", t_total)

        global_step = 0
        tr_loss, logging_loss = 0.0, 0.0
        self.model.zero_grad()
        train_iterator = trange(int(epochs), desc="Epoch", disable=self.local_rank not in [-1, 0])
        num_correct = 0
        label_count = [0] * len(self.config.labels)
        for _ in train_iterator:
            epoch_iterator = tqdm(train_dataloader, desc="Iteration", disable=self.local_rank not in [-1, 0])
            for step, batch in enumerate(epoch_iterator):
                self.model.train()
                correct_labels = batch[3]
                batch = tuple(t.to(self.device) for t in batch)
                inputs = {'input_ids': batch[0],
                          'attention_mask': batch[1],
                          'labels': batch[3]}
                if self.config.base != 'distilbert':
                    inputs['token_type_ids'] = batch[2] if self.config.base in ['bert',
                                                                               'xlnet'] else None
                outputs = self.model(**inputs)
                loss = outputs[0]  # model outputs are always tuple in transformers (see doc)
                logits = outputs[1]
                preds = logits.detach().cpu().numpy()
                preds = np.argmax(preds, axis=1)
                for pred in preds:
                    label_count[pred] += 1
                num_correct += np.sum(preds == correct_labels.numpy())
                if step > 0:
                    epoch_iterator.set_description("Accuracy: %.2f Label Counts: %s"
                                                   % (num_correct / (step*self.batch_size), label_count))
                    epoch_iterator.refresh()  # to show immediately the update

                if self.n_gpu > 1:
                    loss = loss.mean()  # mean() to average on multi-gpu parallel training

                if self.fp16:
                    with amp.scale_loss(loss, optimizer) as scaled_loss:
                        scaled_loss.backward()
                    torch.nn.utils.clip_grad_norm_(amp.master_params(optimizer), self.max_grad_norm)
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)

                tr_loss += loss.item()
                if (step + 1) % self.gradient_accumulation_steps == 0:
                    optimizer.step()
                    scheduler.step()  # Update learning rate schedule
                    self.model.zero_grad()
                    global_step += 1

                    if self.local_rank in [-1, 0] and self.logging_steps > 0 and global_step % self.logging_steps == 0:
                        # Log metrics
                        if self.local_rank == -1 and self.evaluate_during_training:
                            results = self.evaluate(test_dataset)
                            for key, value in results.items():
                                tb_writer.add_scalar('eval_{}'.format(key), value, global_step)
                        tb_writer.add_scalar('lr', scheduler.get_lr()[0], global_step)
                        tb_writer.add_scalar('loss', (tr_loss - logging_loss) / self.logging_steps, global_step)
                        logging_loss = tr_loss

                    if self.local_rank in [-1, 0] and self.save_steps > 0 and global_step % self.save_steps == 0:
                        # Save model checkpoint
                        model_to_save = self.model.module if hasattr(self.model,
                                                                'module') else self.model
                        model_to_save.save_pretrained(self.ckpt_dir)

        if self.local_rank in [-1, 0]:
            tb_writer.close()

        return global_step, tr_loss / global_step

    def evaluate(self, test_dataset):

        eval_dataset = self.load_and_cache_examples(test_dataset, evaluate=True)
        eval_output_dir = os.path.join(self.data_dir, 'eval')

        if not os.path.exists(eval_output_dir) and self.local_rank in [-1, 0]:
            os.makedirs(eval_output_dir)

        # Note that DistributedSampler samples randomly
        eval_sampler = SequentialSampler(eval_dataset) if self.local_rank == -1 else DistributedSampler(
            eval_dataset)
        eval_dataloader = DataLoader(eval_dataset, sampler=eval_sampler, batch_size=self.batch_size)

        # Eval!
        print("***** Running evaluation *****")
        print("  Num examples = ", len(eval_dataset))
        print("  Batch size = ", self.batch_size)
        eval_loss = 0.0
        nb_eval_steps = 0
        preds = None
        out_label_ids = None
        for batch in tqdm(eval_dataloader, desc="Evaluating"):
            self.model.eval()
            batch = tuple(t.to(self.device) for t in batch)

            with torch.no_grad():
                inputs = {'input_ids': batch[0],
                          'attention_mask': batch[1],
                          'labels': batch[3]}
                if self.config.base != 'distilbert':
                    inputs['token_type_ids'] = batch[2] if self.config.base in ['bert',
                                                                               'xlnet'] else None
                outputs = self.model(**inputs)
                tmp_eval_loss, logits = outputs[:2]

                eval_loss += tmp_eval_loss.mean().item()
            nb_eval_steps += 1
            if preds is None:
                preds = logits.detach().cpu().numpy()
                out_label_ids = inputs['labels'].detach().cpu().numpy()
            else:
                preds = np.append(preds, logits.detach().cpu().numpy(), axis=0)
                out_label_ids = np.append(out_label_ids, inputs['labels'].detach().cpu().numpy(), axis=0)

        eval_loss = eval_loss / nb_eval_steps
        result = {
            "loss": eval_loss
        }
        if self.config.task == "classification":
            preds = np.argmax(preds, axis=1)
            result['acc'] = np.sum(preds == out_label_ids) / len(preds)
        elif self.config.task == "regression":
            preds = np.squeeze(preds)

        output_eval_file = os.path.join(eval_output_dir, "eval_results.txt")
        with open(output_eval_file, "w") as writer:
            print("***** Eval results *****")
            for key in sorted(result.keys()):
                print("  %s = %s", key, str(result[key]))
                writer.write("%s = %s\n" % (key, str(result[key])))

        return result

    def convert_example(self, example):
        inputs = self.tokenizer.encode_plus(
            example.text_a,
            example.text_b,
            add_special_tokens=True,
            max_length=self.max_length,
            truncate_first_sequence=True  # We're truncating the first sequence in priority
        )
        return inputs["input_ids"], inputs["token_type_ids"]

    def load_and_cache_examples(self, data, evaluate=False):
        if self.local_rank not in [-1, 0] and not evaluate:
            torch.distributed.barrier()  # Make sure only the first process in distributed training process the dataset, and the others will use the cache

        cached_features_file = os.path.join(self.data_dir, 'features' if not evaluate else 'eval-features')
        if os.path.exists(os.path.join(cached_features_file)):
            print("Loading features from cached file ", cached_features_file)
            features = torch.load(cached_features_file)
        else:
            print("Creating features from dataset file at %s", cached_features_file)
            label_list = self.config.labels

            examples = [
                InputExample(guid=i,
                             text_a=ex[0],
                             text_b=ex[1] if len(ex) == 3 else None,
                             label=ex[-1]) for i, ex in enumerate(data)
            ]
            label_map = {label: i for i, label in enumerate(label_list)}

            features = []
            for (ex_index, example) in enumerate(examples):
                if ex_index % 10000 == 0:
                    print("Writing example %d" % (ex_index))

                input_ids, token_type_ids = self.convert_example(example)

                # The mask has 1 for real tokens and 0 for padding tokens. Only real
                # tokens are attended to.
                attention_mask = [1] * len(input_ids)

                # Zero-pad up to the sequence length.
                padding_length = self.max_length - len(input_ids)
                if self.pad_on_left:
                    input_ids = ([self.pad_token] * padding_length) + input_ids
                    attention_mask = ([1] * padding_length) + attention_mask
                    token_type_ids = ([self.pad_token_segment_id] * padding_length) + token_type_ids
                else:
                    input_ids = input_ids + ([self.pad_token] * padding_length)
                    attention_mask = attention_mask + ([1] * padding_length)
                    token_type_ids = token_type_ids + ([self.pad_token_segment_id] * padding_length)

                assert len(input_ids) == self.max_length, "Error with input length {} vs {}".format(len(input_ids),
                                                                                               self.max_length)
                assert len(attention_mask) == self.max_length, "Error with input length {} vs {}".format(len(attention_mask),
                                                                                                    self.max_length)
                assert len(token_type_ids) == self.max_length, "Error with input length {} vs {}".format(len(token_type_ids),
                                                                                                    self.max_length)
                if self.config.task == "classification":
                    label = label_map[example.label]
                elif self.config.task == "regression":
                    label = float(example.label)
                else:
                    print("Only supported tasks are classification and regression")
                    raise NotImplementedError()

                if ex_index < 5:
                    print("*** Example ***")
                    print("guid: %s" % (example.guid))
                    print("input_ids: %s" % " ".join([str(x) for x in input_ids]))
                    print("attention_mask: %s" % " ".join([str(x) for x in attention_mask]))
                    print("token_type_ids: %s" % " ".join([str(x) for x in token_type_ids]))
                    print("label: %s (id = %d)" % (example.label, label))

                features.append(
                    InputFeatures(input_ids=input_ids,
                                  attention_mask=attention_mask,
                                  token_type_ids=token_type_ids,
                                  label=label))
            if self.local_rank in [-1, 0]:
                print("Saving features into cached file %s", cached_features_file)
                torch.save(features, cached_features_file)

        if self.local_rank == 0 and not evaluate:
            torch.distributed.barrier()  # Make sure only the first process in distributed training process the dataset, and the others will use the cache

        # Convert to Tensors and build dataset
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long)
        all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long)
        if self.config.task == "classification":
            all_labels = torch.tensor([f.label for f in features], dtype=torch.long)
        elif self.config.task == "regression":
            all_labels = torch.tensor([f.label for f in features], dtype=torch.float)
        else:
            raise NotImplementedError()

        dataset = TensorDataset(all_input_ids, all_attention_mask, all_token_type_ids, all_labels)
        return dataset

    def run(self, *args):
        # Protobuffs in and protobuffs out
        batch = self.tokenizer(args[0], args[1])
        return self.model(batch)

    @staticmethod
    def architectures():
        return list(MODEL_CLASSES.keys())
