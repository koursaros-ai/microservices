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
    service.logger.bold(text)
    service.logger.bold(send)
    service.logger.bold(dir(send))
    send(service.Message(text=text))


@service.stub
def send(msg):
    print('Sending')
    # print(msg)
    # print('Sending {}'.format(repr(msg)))
    return msg


if __name__ == "__main__":
    service.run(subs=[app.run])




