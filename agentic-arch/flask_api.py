from flask import Flask, request

app = Flask(__name__)


@app.route('/alert', methods=['POST'])
def alert():
    data = request.get_json(silent=True) or {}
    msg = data.get('msg', '')
    print(f"Received alert: {msg}")
    return f"Alert received: {msg}"


@app.route('/create-task', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    task = data.get('task', '')
    print(f"Received task: {task}")
    return f"Task created: {task}"


if __name__ == '__main__':
    app.run(port=5000)

