from koursaros.pipelines import pig_pipeline
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
import uuid

pipeline = pig_pipeline(__package__)
app = Flask(__name__)
sentences = dict()

backend = pipeline.services.backend
pig = pipeline.services.pig


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
    sentence = backend.stubs.send.Sentence(id=sentence_id, text=text)
    backend.stubs.send.process(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


@backend.stubs.send
def send_sentence(sentence):
    print('SENDING')
    pipeline.services.pig.stubs.piggify(sentence)
    print('SENT')


@backend.stubs.receive
def receive(piggified):
    global sentences
    sentences[piggified.sentence.id].put(piggified.pig_latin)


if __name__ == "__main__":
    s = Thread(target=backend.run)
    a = Thread(target=app.run)

    s.start()
    a.start()
    s.join()
    a.join()


