from koursaros.pipelines import pigservice
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
import uuid

pipeline = piggify(__name__)
app = Flask(__name__)
sentences = dict()


backend_stubs = pipeline.services.backend.stubs
send_stub = backend_stubs.send_sentence


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

    sentence = send_stub.Sentence(id=sentence_id, text=text)
    send_sentence(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


piggify_stub = pipeline.services.pig.stubs.piggify


@send_stub
def send_sentence(sentence):
    piggify_stub(sentence)


@backend_stubs.receive
def receive(piggified):
    global sentences
    sentences[piggified.sentence.id].put(piggified.pig_latin)


if __name__ == "__main__":
    s = Thread(target=pipeline.services.backend.run)
    a = Thread(target=app.run)

    s.start()
    a.start()
    s.join()
    a.join()


