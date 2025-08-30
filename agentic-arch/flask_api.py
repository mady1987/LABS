from flask import Flask, request

app = Flask(__name__)

@app.route('/alert', methods=['POST'])
def alert():
    data = request.json or {}
    return f"✅ Alert received: {data.get('msg','')}"

@app.route('/create-task', methods=['POST'])
def task():
    data = request.json or {}
    return f"📍 Task created: {data.get('task','')}"

if __name__ == '__main__':
    app.run(port=5000)
