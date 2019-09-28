from koursaros import Service
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
import uuid

service = Service(__file__)
app = Flask(__name__)
sentences = dict()


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

    sentence = service.messages.Sentence(id=sentence_id, text=text)
    send_sentence(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


@service.stub('send')
def send_sentence(sentence, publish):
    publish(sentence)


@service.stub('receive')
def receive(piggified, publish):
    global sentences
    sentences[piggified.sentence.id].put(piggified.pig_latin)


if __name__ == "__main__":
    s = Thread(target=service.run)
    a = Thread(target=app.run)

    s.start()
    a.start()
    s.join()
    a.join()


