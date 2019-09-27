from koursaros import Service
from flask import Flask, request, jsonify
from queue import Queue
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
    return jsonify({
        "status": "failure",
        "msg": "Please provide a sentence"
    })
    global sentences

    print('SENDING sdjfzohjfodsf')
    sentence_id = str(uuid.uuid4())
    print('saodifhlasfgoe FUUUUUUCK')
    queue = Queue()
    print('SENDING :)')
    sentences[sentence_id] = queue

    print('SENDING FUUUUUUCK')
    sentence = service.messages.Sentence(id=sentence_id, text=text)
    print('SENDING FUUUUUUCK')
    send(sentence)
    print('MADE FUUUUUUCK')
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })


@service.stubs.send_sentence
def send(sentence, publish):
    print(sentence)
    publish(sentence)


@service.stubs.receive
def receive(piggified, publish):
    print(piggified)
    global sentences
    sentences[piggified.sentence.id].put(piggified.pig_latin)


def main():
    app.run()
