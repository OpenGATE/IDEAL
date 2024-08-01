from flask import request, jsonify, Response
from apiflask import APIFlask, HTTPTokenAuth, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os, stat
import jwt
from utils.api_schemas import Authentication

app = APIFlask(__name__,title='Mock receiver', version='1.0')
auth = HTTPTokenAuth(scheme='Bearer')

# api configuration
app.config['SECRET_KEY'] = os.urandom(24)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////opt/share/IDEAL-1_1dev/database_receiver.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# register database 
db = SQLAlchemy(app)

class User(db.Model):
   uid = db.Column(db.Integer, primary_key = True)
   username = db.Column(db.String())
   password = db.Column(db.String())
   firstname = db.Column(db.String(50))
   lastname = db.Column(db.String(100))
   role = db.Column(db.String())
    
   def __init__(self, username, pwd, firstname, lastname, role):
       self.username = username
       self.password = generate_password_hash(pwd)
       self.role = role 
       self.firstname = firstname
       self.lastname = lastname
       

@app.route("/api/results/<jobId>", methods=['POST'])
@app.auth_required(auth)
def receive(jobId):
    plan_file = request.files.get('monteCarloDoseDicom')
    log_file = request.files.get('logFile')
    
    print(plan_file.filename)
    base_out_dir = "/var/output/IDEAL-1_1dev/"
    out_dir = os.path.join(base_out_dir,jobId)
    os.mkdir(out_dir)
    plan_file.save(os.path.join(out_dir,secure_filename(plan_file.filename)))
    
    print(log_file.filename)
    log_file.save(os.path.join(out_dir,secure_filename(log_file.filename)))
    
    # change ownership of folder to ideal and group access
    for file in os.listdir(out_dir) + [out_dir]:
        f = os.path.join(out_dir,file)
        os.chown(f,-1,1060) # ideal gid = 1060
        mode = os.stat(out_dir).st_mode # current mode
        os.chmod(f,mode | stat.S_IRWXG)
        
    return 'ok'

@auth.verify_token
def verify_tocken(token): 
    if token is None:
        abort(401, message='Invalid token')
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = User.query.filter_by(uid=data['public_id']).first()
    except:
        abort(401, message='Invalid token')
  
    if current_user is None:
       abort(401, message='Invalid token')

    return current_user
    

@app.route("/auth", methods=['GET'])
@app.input(Authentication,location = 'headers')
def authentication(auth):
    username = auth.get('account-login')
    print(username)
    pwd = auth.get('account-pwd')
    print(pwd)
    user = User.query.filter_by(username=username).first()
    if not user:
        return abort(401, message='Could not verify user!', detail={'WWW-Authenticate': 'Basic-realm= "No user found!"'})
    
    if not check_password_hash(user.password, pwd):
        return abort(403, message='Could not verify password!', detail= {'WWW-Authenticate': 'Basic-realm= "Wrong Password!"'})
    
    token = jwt.encode({'public_id': user.uid}, app.config['SECRET_KEY'], 'HS256')

    return jsonify({'authToken': token, 'username':user.username}), 201 

# initialize database
with app.app_context():
    db.create_all()
    fava = User('fava','Password456','Martina','Favaretto','commissioning')
    myqaion = User('admin','IDEALv1.1','Myqa','Ion','clinical')
    db.session.add(fava)
    db.session.add(myqaion)
    db.session.commit()

app.run(host="10.2.72.75", port=3000) #,ssl_context='adhoc')
