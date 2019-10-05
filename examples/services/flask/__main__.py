from koursaros import Service
from flask import Flask, request, jsonify


service = Service(__package__)
app = Flask(__name__)


@app.route('/')
def receive():
    text = request.args.get('q')
    if not text:
        return jsonify({
            "status": "failure",
            "msg": "Please provide a msg"
        })

    send(service.Message(text=text))


@service.stub
def send(msg):
    print('Sending ' + msg)
    return msg


@service.callback
def callback(msg):
    print('Received ' + msg)


if __name__ == "__main__":
    service.run(subs=[app.run])




