from koursaros.service import Service
from flask import Flask, request, jsonify


service = Service()
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
    print('Sending %s' % msg)
    return msg


if __name__ == "__main__":
    service.run(subs=[app.run])




