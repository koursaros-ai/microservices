<img src=".github/koursaros.jpg" alt="Koursaros">

<hr/>

<p align="center">
<a href='https://github.com/koursaros-ai/koursaros/blob/master/LICENSE'>
    <img alt="PyPI - License" src="https://img.shields.io/badge/license-MIT-green.svg">
</a>
</p>

<p align="center">
  <a href='https://koursaros-ai.github.io'>Blog</a> •
  <a href="#highlights">Highlights</a> •
  <a href="#overview">Overview</a> •
  <a href="#install">Install</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#tutorials">Tutorials</a> •
  <a href="#contributing">Contributing</a>
</p>

Koursaros is a distributed, cloud-native platform for developing and deploying neural search and inference applications.

Koursaros leverages a general-purpose microservice / broker architecture to enable low-latency, scalable deep neural network training and can be directly deployed to kubernetes for production.

## Results

<table>
  <tr>
    <th>Benchmark</th>
    <th>Label Accuracy</th>
    <th>Paper</th>
    <th>Models</th>
  </tr>
  <tr>
    <td><a href="http://fever.ai">fever.ai</a>
    <td>0.7396 (2nd)</td>
    <td><a href='https://koursaros-ai.github.io/Live-Fact-Checking-Algorithms-in-the-Era-of-Fake-News/'>An Automated Fact Checker in Era of Fake News</a></td>
    <td>coming soon</td>
  </tr>
</table>

## Install
### Requirements
You need Python 3.6 or later to run Koursaros.

### Stable Version
#### Installing via pip
We recommend installing Koursaros via pip:
```
pip3 install koursaros
```
Installation will use Python wheels from PyPI, available for OSX, Linux, and Windows.

### Latest Version
### Installing via pip-git
You can install the latest version from Git:
```
pip3 install git+https://git@github.com/koursaros-ai/koursaros.git
```

## Getting Started
### Creating a pipeline
```
kctl pull app my-app --git koursaros --dir examples/simple-app
cd my-app
kctl deploy app
```

Then open [http://localhost:5200/](http://localhost:5200/) to see your pipeline running!

This simple pipeline has three microservices: a sender, preprocesser, and model.
The sender sends a request to factor a number: "Please factor 12!".
The preprocesser receives this request and extracts the number.
The model gets only the number, factors it, and sends it back to the sender.

kctl created a directory called MyPipeline with the following project structure:

```
my-app
├── README.md
├── .gitignore
├── services
│   ├── sender
│   └── model
├── pipelines
│   └── factor-number
│       ├── stubs.yaml
│       └── messages.proto
└── models
    └── factorer.py
```

Now let's create a new microservice called counter.
Counter will just count the number of factors before sending the factors to the sender.

First, we need add the counter to the ```stubs.yaml```.
Let's say the counter will receive the Factors message and will return a FactorsWithCount message.
<table>
<tr>
<th>Before</th>
<th>After</th>
</tr>
<tr>
<td width="30%">
   <sub>
   <pre lang="yaml">
stubs:
 send: sender.request() -> Number                     | factor
 factor: model.factor(Number) -> Factors              | sendback
 sendback: sender.receive(Factors)                  ->|
   </pre>
   </sub>
</td>
<td width="30%">
   <sub>
   <pre lang="yaml">
stubs:
 send: sender.request() -> Number                     | factor
 factor: model.factor(Number) -> Factors              | count
 count: counter.count(Factors) -> FactorsWithCount    | sendback
 sendback: sender.receive(Factors)                  ->|
   </pre>
   </sub>
</td>
</tr>
</table>

Now let's generate the service script:
```
kctl create service counter
```
This creates a new service called counter in the services directory.
Let's look at its ```__init__.py```:
<table>
<tr>
<th>Before</th>
<th>After</th>
</tr>
<tr>

<td width="30%">

   <pre lang="python">
from koursaros import Service

service = Service(__name__)


@service.pubber
def send(publish):
    pass


@service.subber
def process(proto, publish):
    pass


@service.main
def main(connection):
    if connection == 'dev_local':
        pass
   </pre>

</td>
<td width="30%">
    
   <pre lang="python">
from koursaros import Service
from ..messages import FactorsWithCount

service = Service(__name__)


@service.subber
def process(factors, publish):
    count = len(factors.factors)
    factors_with_count = FactorsWithCount(
        factors=factors.factors,
        count=count
    )
    publish(factors_with_count)


@service.main
def main(connection):
    if connection == 'dev_local':
        pass
   </pre>
    

</td>
</tr>
</table>

Then we need add the FactorsWithCount to the ```messages.proto```:

<table>
<tr>
<th>Before</th>
<th>After</th>
</tr>
<tr>

<td width="30%">

   <pre lang="proto">
message Request {
    uint64 id = 1;
    string text = 2;
}

message Number {
    uint64 request_id = 1;
    uint64 number = 2;
}

message Factors {
    uint64 request_id = 1;
    repeated Number numbers = 2;
}
   </pre>

</td>
<td width="30%">
    
   <pre lang="proto">
message Request {
    uint64 id = 1;
    string text = 2;
}

message Number {
    uint64 request_id = 1;
    uint64 number = 2;
}

message Factors {
    uint64 request_id = 1;
    repeated Number numbers = 2;
}

message FactorsWithCount {
    uint64 request_id = 1;
    repeated Number numbers = 2;
    uint64 count = 3;
}
   </pre>
    

</td>
</tr>
</table>

Now start your app again with ```kctl deploy app``` and see the changes!
    
## Tutorials
- <a href = 'tutorials/fact_check.md'>Use Koursaros to get SoTA results in dev environment</a> on the <a href='fever.ai'>fever.ai</a> benchmark using pretrained models.
- <a href = 'tutorials/deploy_custom_model.md'>Training custom models and deploying them as stubs</a>
- Training Elastic Search BM25 algorithm using Ax Bayesian Optimizer (coming soon)
- Deploying fever.ai pipeline to production (Coming Soon)
