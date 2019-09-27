from koursaros import Service
from flask import Flask, request, jsonify
from queue import Queue
import threading
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
    send(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


@service.stub
def send_sentence(sentence, publish):
    print(sentence)
    publish(sentence)


@service.stub
def receive(piggified, publish):
    print(piggified)
    global sentences
    sentences[piggified.sentence.id].put(piggified.pig_latin)


def main():
    threads = service.run()
    threads.append(threading.Thread(target=app.run))

    for t in threads:
        t.start()

    for t in threads:
        t.join()
