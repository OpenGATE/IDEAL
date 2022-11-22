from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def welcome():
    return "Hello there"

@app.route("/results/<jobId>", methods=['POST'])
def receive(jobId):
    plan_file = request.files.get('monteCarloDoseDicom')
    print(plan_file.filename)
    plan_file.save("/user/fava/Test_api_filetransfer/"+jobId+"_"+plan_file.filename)
    
    log_file = request.files.get('logFile')
    print(log_file.filename)
    plan_file.save("/user/fava/Test_api_filetransfer/"+jobId+"_"+log_file.filename)
    return 'ok'

app.run(port=3000)