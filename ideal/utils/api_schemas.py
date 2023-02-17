from apiflask import Schema
from marshmallow import validates_schema, ValidationError
from apiflask.fields import Float, Integer, String, File


class SimulationRequest(Schema):
    dicomRtPlan = File(required=True, metatdata={'description': 'Zipped RT dicom plan'})
    dicomStructureSet = File(required=True, metatdata={'description': 'Zip file containing the Structure files'})
    dicomCTs = File(required=True, metatdata={'description': 'Zip file containing the CT files'})
    dicomRDose = File(required=True, metatdata={'description': 'Zip file containing the Dose files'})
    uncertainty = Float(load_default = 0)
    numberOfParticles = Integer(load_default = 0)
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
    
