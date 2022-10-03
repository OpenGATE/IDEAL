from crypt import methods
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def welcome():
    return "Hello there"

@app.route("/result", methods=['POST'])
def receive():
    file = request.files.get('result')
    print(file.filename)
    file.save("/home/username/IRECEIVEDTHISFILE")
    return file.filename

app.run(port=3000)