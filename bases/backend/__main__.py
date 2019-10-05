from koursaros.pipelines import factchecking
from flask import Flask, request, jsonify, render_template
from queue import Queue
from threading import Thread
import uuid
import os

pipeline = factchecking(__file__)
print(os.getcwd())
app = Flask(
    __name__,
    static_folder=__file__ + 'fever/build/static',
    template_folder=__file__ + "fever/build"
)

sentences = dict()

backend = pipeline.services.backend
elastic = pipeline.services.elastic


@app.route('/')
def serve():
    return render_template('index.html')


@app.route('/query')
def receive():
    text = request.args.get('q')
    if not text:
        return jsonify({
            "status": "failure",
            "msg": "Please provide a sentence"
        })
    global sentences

    sentence_id = str(uuid.uuid4())
    queue = Queue()
    sentences[sentence_id] = queue

    sentence = backend.stubs.send.Claim(id=sentence_id, text=text)
    backend.stubs.send(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
    })


@backend.stubs.send
def send_sentence(sentence):
    elastic.stubs.retrieve(sentence)


@backend.stubs.receive
def receive(evaluated):
    global sentences
    response = {
        "label": evaluated.label,
        "evidence": [line for line in evaluated.evidence]
    }
    sentences[evaluated.claim.id].put(response)


if __name__ == "__main__":
    b = Thread(target=backend.run)
    a = Thread(target=app.run, kwargs={'host': '0.0.0.0'})

    b.start()
    a.start()

    b.join()
    a.join()
