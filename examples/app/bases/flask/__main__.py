from koursaros.service import Service
from flask import Flask, request, jsonify
from queue import Queue


service = Service()
app = Flask(__name__)

FAILURE = dict(status='failure', msg='Please provide a msg')

queue = Queue()


@app.route('/')
def receive():
    global queue

    texta = request.args.get('a')
    textb = request.args.get('b')
    if not (texta and textb):
        return jsonify(FAILURE)

    send(service.Message(text=[texta, textb]))
    return jsonify(dict(status='success', msg=queue.get()))


@service.stub
def send(msg):
    # service.logger.info('Sending %s' % msg)
    return msg


@service.callback
def callback(msg):
    global queue
    queue.put(msg.label)


if __name__ == "__main__":
    service.run(subs=[app.run])




