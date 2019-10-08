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

    text = request.args.get('q')
    if not text:
        return jsonify(FAILURE)

    send(service.Message(text=text))
    return jsonify(dict(status='success', msg=queue.get()))


@service.stub
def send(msg):
    # service.logger.info('Sending %s' % msg)
    return msg


@service.callback
def callback(msg):
    global queue
    queue.put(msg.text)


if __name__ == "__main__":
    service.run(subs=[app.run])




