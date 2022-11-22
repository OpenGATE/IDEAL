from flask import Flask, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route("/")
def welcome():
    return "Hello there"

@app.route("/results/<jobId>", methods=['POST'])
def receive(jobId):
    plan_file = request.files.get('monteCarloDoseDicom')
    log_file = request.files.get('logFile')
    
    print(plan_file.filename)
    plan_file.save("/user/fava/Test_api_filetransfer/"+jobId+"_"+secure_filename(plan_file.filename))
    
    print(log_file.filename)
    log_file.save("/user/fava/Test_api_filetransfer/"+jobId+"_"+secure_filename(log_file.filename))
    return 'ok'

app.run(port=3000)