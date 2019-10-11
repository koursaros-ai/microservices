from ..model import Model
import torch.nn, torch.tensor, torch.distributed, torch.jit
from transformers import *
from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,
                              TensorDataset, DistributedSampler)
from tensorboardX import SummaryWriter
from tqdm import tqdm
import numpy as np
import os
from kctl.logger import set_logger
import torch.nn.functional as F

from koursaros.utils.misc import batch_list

logger = set_logger('MODELS')

MODEL_CLASSES = {
    'bert': (BertConfig, BertForSequenceClassification, BertTokenizer),
    'xlnet': (XLNetConfig, XLNetForSequenceClassification, XLNetTokenizer),
    'xlm': (XLMConfig, XLMForSequenceClassification, XLMTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForSequenceClassification, DistilBertTokenizer)
}

class TransformerModel(Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        if self.config.task == 'classification' or self.config.task == 'regression':
            config, model, tokenizer = MODEL_CLASSES[self.config.arch]
        else:
            raise NotImplementedError()

        self.model_config = config.from_pretrained(self.checkpoint, cache_dir=self.dir)
        self.model = model.from_pretrained(self.checkpoint, config=self.model_config,
                                           cache_dir=self.dir, **kwargs)
        self.tokenizer = tokenizer.from_pretrained(self.checkpoint, cache_dir=self.dir)
        self.batch_size = self.config.training.batch_size
        self.max_grad_norm = 1.0
        self.weight_decay = 0.0
        self.n_gpu = 1
        self.local_rank = -1
        self.gradient_accumulation_steps = 1
        self.max_length = 512
        self.fp16 = False
        self.evaluate_during_training = True
        self.pad_token_segment_id = 4 if self.config.arch == 'xlnet' else 0
        self.pad_on_left = True
        self.pad_token = 0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.pad = True
        if self.trained:
            self.model.eval()
            # self.trace_model()
        if self.config.task == 'classification':
            self.model_config.num_labels = len(self.config.labels)
            self.label_map = {label: i for i, label in enumerate(self.config.labels)}
            self.best_checkpoint_metric = 'acc'
        elif self.config.task == 'regression':
            self.best_checkpoint_metric = 'loss'

    def inputs_from_batch(self, batch):
        inputs = {'input_ids': batch[0],
                  'attention_mask': batch[1]}
        if self.config.arch != 'distilbert':
            inputs['token_type_ids'] = batch[2] if self.config.arch in ['bert',
                                                                        'xlnet'] else None
        if len(batch) > 3:
            inputs['labels'] = batch[3]
        return inputs

    def tuple_inputs(self, inputs):
        return (
            inputs['input_ids'],
            inputs['attention_mask'],
            inputs['token_type_ids']
        )

    def trace_model(self):
        examples = [
            InputExample(
                guid=1,
                text_a="Once upon a time there was a boy",
                text_b="He liked to write code all day long"
            )
        ]
        features = [self.example_to_feature(example) for example in examples]
        all_inputs = self.features_to_inputs(features, True)
        inputs = self.inputs_from_batch(all_inputs)
        self.model = torch.jit.trace(self.model, self.tuple_inputs(inputs))

    def train(self, force_build_features=False):
        return self.do_train(force_build_features=force_build_features)
        # except:
        #     logger.warning('Error during training, decrease batch size and try again')
        #     raise SystemError()
        #     self.batch_size = self.batch_size // 2 # back off batch_size
        #     return self.train(force_build_features=True)

    def do_train(self, force_build_features=False):
        ### In Transformers, optimizer and schedules are splitted and instantiated like this:

        tb_writer = SummaryWriter()

        train_dataset, test_dataset = self.get_data()
        train_dataset = self.load_and_cache_examples(train_dataset, force_build_features=force_build_features)
        epochs = int(self.config.training.epochs)
        optimizer = AdamW(self.model.parameters(), lr=float(self.config.training.learning_rate),
                          correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
        num_warmup_steps = int(0.06 * len(train_dataset))
        scheduler = WarmupLinearSchedule(optimizer, warmup_steps=num_warmup_steps,
                                         t_total=(self.config.training.epochs * len(train_dataset) / self.batch_size))

        train_sampler = RandomSampler(train_dataset)
        train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=self.batch_size)

        t_total = len(train_dataloader)

        # Prepare optimizer and schedule (linear warmup and decay)
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
             'weight_decay': self.weight_decay},
            {'params': [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)],
             'weight_decay': 0.0}
        ]

        try:
            from apex import amp
            model, optimizer = amp.initialize(self.model, optimizer)
            self.fp16 = True
        except ImportError:
            logger.warning("Please install fp16 from https://github.com/NVIDIA/apex for better performance")
            self.fp16 = False

        # Train!
        logger.info("***** Running training *****")
        logger.info("  Num examples = %d" % len(train_dataset))
        logger.info("  Num Epochs = %d" % epochs)
        logger.info("  Total train batch size (w. parallel, distributed & accumulation) = %d" %
                    self.batch_size * (
                        torch.distributed.get_world_size() if self.local_rank != -1 else 1))
        logger.info("  Total optimization steps = %d" % t_total)

        if not 'eval_freq' in self.config.training:
            self.eval_freq = 2
        else:
            self.eval_freq = self.config.training.eval_freq

        self.eval_and_save_every = len(train_dataset) // self.batch_size // self.eval_freq

        global_step = 0
        tr_loss, logging_loss = 0.0, 0.0
        self.model.zero_grad()
        if self.config.task == 'classification':
            label_count = [0] * len(self.config.labels)
            num_correct = 0
        epoch_iterator = tqdm(train_dataloader, desc="Iteration", disable=self.local_rank not in [-1, 0])
        prev_best = None
        for step, batch in enumerate(epoch_iterator):
            self.model.train()
            correct_labels = batch[3]
            batch = tuple(t.to(self.device) for t in batch)

            inputs = self.inputs_from_batch(batch)
            outputs = self.model(**inputs)
            loss = outputs[0]  # model outputs are always tuple in transformers (see doc)
            logits = outputs[1]
            preds = logits.detach().cpu().numpy()
            preds = np.argmax(preds, axis=1)

            if self.config.task == 'classification':
                for pred in preds:
                    label_count[pred] += 1
                num_correct += np.sum(preds == correct_labels.detach().cpu().numpy())
                if step > 0:
                    epoch_iterator.set_description("Accuracy: %.2f Label Counts: %s"
                                                   % (num_correct / (step * self.batch_size), label_count))
                    epoch_iterator.refresh()  # to show immediately the update
            if self.config.rask == 'regression' and step > 0:
                epoch_iterator.set_description("Loss: %.2f" % loss)
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

                if self.local_rank in [-1, 0]  and global_step % self.eval_and_save_every == 0:
                    # Log metrics
                    if self.local_rank == -1 and self.evaluate_during_training:
                        results = self.evaluate(test_dataset)
                        for key, value in results.items():
                            tb_writer.add_scalar('eval_{}'.format(key), value, global_step)
                        tb_writer.add_scalar('lr', scheduler.get_lr()[0], global_step)
                        tb_writer.add_scalar('loss', (tr_loss - logging_loss) / self.eval_and_save_every, global_step)
                        logging_loss = tr_loss
                        if prev_best is None or results[self.best_checkpoint_metric] > prev_best:
                            prev_best = results[self.best_checkpoint_metric]
                            self.save_model()

        if self.local_rank in [-1, 0]:
            tb_writer.close()

        result = self.evaluate(test_dataset)
        if prev_best is None or result[self.best_checkpoint_metric] > prev_best:
            self.save_model()

        return global_step, tr_loss / global_step

    def save_model(self):
        # Save model checkpoint
        model_to_save = self.model.module if hasattr(self.model,
                                                     'module') else self.model
        model_to_save.save_pretrained(self.ckpt_dir)
        self.tokenizer.save_pretrained(self.ckpt_dir)

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
        logger.info("***** Running evaluation *****")
        logger.info("  Num examples = %d" % len(eval_dataset))
        logger.info("  Batch size = %d" % self.batch_size)
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
                if self.config.arch != 'distilbert':
                    inputs['token_type_ids'] = batch[2] if self.config.arch in ['bert',
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
            logger.info("***** Eval results *****")
            for key in sorted(result.keys()):
                logger.info("  %s = %s" % (key, str(result[key])))
                writer.write("%s = %s\n" % (key, str(result[key])))

        return result

    def example_to_feature(self, example):
        inputs = self.tokenizer.encode_plus(
            example.text_a,
            example.text_b,
            add_special_tokens=True,
            max_length=self.max_length,
            truncate_first_sequence=True  # We're truncating the first sequence in priority
        )
        input_ids, token_type_ids = inputs["input_ids"][:self.max_length], \
                                    inputs["token_type_ids"][:self.max_length]

        attention_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        if self.pad:
            padding_length = self.max_length - len(input_ids)
            if self.pad_on_left:
                input_ids = ([self.pad_token] * padding_length) + input_ids
                attention_mask = ([0] * padding_length) + attention_mask
                token_type_ids = ([self.pad_token_segment_id] * padding_length) + token_type_ids
            else:
                input_ids = input_ids + ([self.pad_token] * padding_length)
                attention_mask = attention_mask + ([0] * padding_length)
                token_type_ids = token_type_ids + ([self.pad_token_segment_id] * padding_length)

        if example.label is not None:
            if self.config.task == "classification":
                if example.label in self.label_map:
                    label = self.label_map[example.label]
                else:
                    logger.warning("UNKNOWN LABEL %s, ignoring" % example.label)
                    return
            elif self.config.task == "regression":
                label = float(example.label)
            else:
                logger.error("Only supported tasks are classification and regression")
                raise NotImplementedError()
        else:
            label = None

        return InputFeatures(input_ids=input_ids,
                          attention_mask=attention_mask,
                          token_type_ids=token_type_ids,
                          label=label)


    def to_features(self, *args):
        inputs = self.tokenizer.encode_plus(
            *args,
            add_special_tokens=True,
            max_length=self.max_length,
            truncate_first_sequence=True
        )
        input_ids = inputs["input_ids"][:self.max_length]
        return input_ids


    def features_to_inputs(self, features, inference):
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long).to(self.device)
        all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long).to(self.device)
        all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long).to(self.device)
        if not inference:
            if self.config.task == "classification":
                all_labels = torch.tensor([f.label for f in features], dtype=torch.long).to(self.device)
            elif self.config.task == "regression":
                all_labels = torch.tensor([f.label for f in features], dtype=torch.float).to(self.device)
            else:
                raise NotImplementedError()
            return all_input_ids, all_attention_mask, all_token_type_ids, all_labels
        else:
            return all_input_ids, all_attention_mask, all_token_type_ids


    def pad_up(self, input_ids, max_length):
        padding_length = max_length - len(input_ids)
        attention_mask = ([0] * padding_length) + [1] * len(input_ids)
        input_ids = ([0] * padding_length) + input_ids
        return (input_ids, attention_mask)


    def transformers_encode_batch(self, *args):
        assert (type(args[0]) == list or type(args[0]) == tuple)
        all_input_ids = []
        max_batch_len = 0

        for sample in zip(*args):
            input_ids = self.to_features(*sample)
            all_input_ids.append(input_ids)
            max_batch_len = max(max_batch_len, len(input_ids))

        all_input_ids, all_attention_masks = zip(*[
            self.pad_up(input_ids, max_batch_len) for input_ids in all_input_ids
        ])
        return all_input_ids, all_attention_masks


    def load_and_cache_examples(self, data, evaluate=False, force_build_features=False):
        if self.local_rank not in [-1, 0] and not evaluate:
            torch.distributed.barrier()  # Make sure only the first process in distributed training process the dataset, and the others will use the cache

        cached_features_file = os.path.join(self.data_dir, 'features' if not evaluate else 'eval-features')
        if os.path.exists(os.path.join(cached_features_file)) and not force_build_features:
            logger.info("Loading features from cached file %s" % cached_features_file)
            features = torch.load(cached_features_file)
        else:
            logger.info("Creating features from dataset file at %s" % cached_features_file)

            examples = [
                InputExample(guid=i,
                             text_a=ex[0],
                             text_b=ex[1] if len(ex) == 3 else None,
                             label=ex[-1]) for i, ex in enumerate(data)
            ]

            features = []
            for (ex_index, example) in enumerate(examples):
                if ex_index % 10000 == 0:
                    logger.info("Writing example %d" % (ex_index))
                features.append(self.example_to_feature(example))

            if self.local_rank in [-1, 0]:
                logger.info("Saving features into cached file %s" % cached_features_file)
                torch.save(features, cached_features_file)

        if self.local_rank == 0 and not evaluate:
            torch.distributed.barrier()  # Make sure only the first process in distributed training process the dataset, and the others will use the cache

        # Convert to Tensors and build dataset
        dataset = TensorDataset(*self.features_to_inputs(features, False))
        return dataset

    def run(self, *args):
        inputs = self.transformers_encode_batch(*args)
        inputs_dict = {
            'input_ids': torch.tensor(inputs[0], dtype=torch.long).to(self.device),
            'attention_mask': torch.tensor(inputs[1], dtype=torch.long).to(self.device),
        }
        outputs = self.model(inputs_dict['input_ids'], inputs_dict['attention_mask'])
        logits = outputs[0]
        if self.config.task == 'classification':
            preds = logits.argmax(dim=1)
            return [self.config.labels[int(pred)] for pred in preds]
        elif self.config.task == 'regression':
            return logits.squeeze().item()

    def multi_gpu_training(self):
        # multi-gpu training (should be after apex fp16 initialization)
        if self.n_gpu > 1:
            model = torch.nn.DataParallel(self.model)
        # Distributed training (should be after apex fp16 initialization)
        if self.local_rank != -1:
            model = torch.nn.parallel.DistributedDataParallel(self.model, device_ids=[self.local_rank],
                                                              output_device=self.local_rank,
                                                              find_unused_parameters=True)

    @staticmethod
    def architectures():
        return list(MODEL_CLASSES.keys())
