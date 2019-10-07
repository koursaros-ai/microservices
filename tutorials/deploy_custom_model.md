# Training + Deploying a Custom Transformer Model in 5 Minutes

## Training Sentence Classification or Regression

Make sure you've installed the koursaros training package.

Create a <name>.yaml file for your model in the /services directory. Your project should look like:

```
   |-bases/
   |-pipelines/
   |---my_pipeline.yaml
   |-services/
   |---[name].yaml
```

For loading mnli from a postgres table, the yaml file should look like this:
```yaml
service:
  base: <bert|roberta|xlnet|distilibert|xlm>
  repo: gs://<your-bucket-name>
  task: <classification|regression>
  labels: # if classification, else nothing
    - neutral
    - contradiction
    - entailment
  training:
    checkpoint: bert-base-uncased # see transformers for options, or use custom filename
    epochs: 3
    learning_rate: 1e-05
```

### Loading data from postgresql

For loading training data form postgres (recommended), add this to the service yaml. Adjust the schema and tables to point your your train / test data.
```yaml
  data:
    source: postgres
    schema: mnli
    train: train_set
    test: test_set
```

And adjust your environment variables accordingly:
```bash
export PGHOST=
export PGUSER=
export PGPASS=
export PGDBNAME=
# for ssl
export PGSSLMODE=verify-ca
export PGSSLROOTCERT=
```

### Loading data from tsv / excel

```yaml
data:
    source: tsv
    train: train_set.tsv
    test: test_set.tsv
```

---

**NOTE**

The format for tables or TSV files for training should be `<text_a, optional_text_b, label>`

---

### Run training and push model to bucket

Run `kctl train services/mnli.yaml`. The model will be cached locally, unless you specify a google storage bucket to upload to for deployment. Read about authentication in the google cloud storage API.

## Deploying



### Set up App

## 