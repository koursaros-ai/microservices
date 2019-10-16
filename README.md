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

Koursaros is a distributed cloud platform for developing and deploying neural search and inference applications.

Koursaros leverages a general-purpose microservice architecture to enable low-latency, scalable deep neural network training and can be directly deployed to kubernetes for production.

## Description
This is page is a work in progress.

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
kctl deploy app
```

   
## Tutorials
- <a href = 'tutorials/fact_check.md'>Use Koursaros to get SoTA results in dev environment</a> on the <a href='fever.ai'>fever.ai</a> benchmark using pretrained models.
- <a href = 'tutorials/deploy_custom_model.md'>Training custom models and deploying them as stubs</a>
- Training Elastic Search BM25 algorithm using Ax Bayesian Optimizer (coming soon)
- Deploying fever.ai pipeline to production (Coming Soon)
