from koursaros.pipelines import pig_pipeline
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
import uuid

Pipeline = pig_pipeline(__package__)
app = Flask(__name__)
sentences = dict()

backend = Pipeline.Services.backend
pig = Pipeline.Services.pig


@app.route('/')
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
    sentence = backend.Stubs.send.Sentence(id=sentence_id, text=text)
    backend.Stubs.send.process(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


@backend.Stubs.send
def send_sentence(sentence):
    print(sentence)
    return sentence


@backend.Stubs.receive
def receive(piggified):
    global sentences
    print(sentences)
    sentences[piggified.sentence.id].put(piggified.pig_latin)


if __name__ == "__main__":
    s = Thread(target=backend.run)
    a = Thread(target=app.run)

    s.start()
    a.start()
    s.join()
    a.join()


