from apiflask import Schema
from marshmallow import validates_schema, ValidationError
from apiflask.validators import Range
from apiflask.fields import Float, Integer, String, File
from werkzeug.security import  generate_password_hash

class SimulationRequest(Schema):
    dicomRtPlan = File(required=True, metatdata={'description': 'Zipped RT dicom plan'})
    dicomStructureSet = File(required=True, metatdata={'description': 'Zip file containing the Structure files'})
    dicomCTs = File(required=True, metatdata={'description': 'Zip file containing the CT files'})
    dicomRDose = File(required=True, metatdata={'description': 'Zip file containing the Dose files'})
    uncertainty = Float(load_default = 0, validate = Range(min=0,max=100,min_inclusive=False,max_inclusive=True))
    numberOfParticles = Integer(load_default = 0, validate = Range(min=0,min_inclusive=False))
    username = String(required=True)
    configChecksum = String(required=True)
    
    phantom = String()
    
    @validates_schema
    def validate_stopping_criteria(self,data,**kwargs):
        if 'uncertainty' not in data and 'numberOfParticles' not in data:
            raise ValidationError('provide at least one stopping criteria. Available are: uncertainty, numberOfParticles')

class Authentication(Schema):
    account_login = String(required=True)
    account_pwd = String(required=True)
  
def define_user_model(db):
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
           
    return User

# # initialize database
# with app.app_context():
#     db.create_all()
#     fava = User('fava','Password456','Martina','Favaretto','commissioning')
#     myqaion = User('myqaion','Password123','Myqa','Ion','clinical')
#     db.session.add(fava)
#     db.session.add(myqaion)
#     db.session.commit()