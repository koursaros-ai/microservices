from koursaros import Service
from flask import Flask, request, jsonify, render_template
from queue import Queue
import threading
import uuid
import os

service = Service(__file__)
print(os.getcwd())
app = Flask(__name__, static_folder='/home/jp954/koursaros/examples/apps/flask-service/fact-check/fever/build/static',
            template_folder="/home/jp954/koursaros/examples/apps/flask-service/fact-check/fever/build")
sentences = dict()


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

    sentence = service.messages.Claim(id=sentence_id, text=text)
    send_sentence(sentence)
    return jsonify({
        "status": "success",
        "msg": queue.get()
        })

@service.stub
def send_sentence(sentence, publish):
    publish(sentence)


@service.stub
def receive(evaluated, publish):
    global sentences
    response = {
        "label" : evaluated.label,
        "evidence" : [line for line in evaluated.evidence]
    }
    sentences[evaluated.claim.id].put(response)


def main():
    threads = service.run()
    threads.append(threading.Thread(target=app.run, kwargs={'host':'0.0.0.0'}))

    for t in threads:
        t.start()

    for t in threads:
        t.join()