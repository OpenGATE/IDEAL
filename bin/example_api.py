from ideal_module import * 
import os
from utils.condor_utils import zip_files
import requests
from zipfile import ZipFile


def main():
    # get rp folder
    plan_dir = '/home/fava/TPSdata/IR2_hbl_CTcase_1beamsets_1beam'
    os.chdir(plan_dir)
    
    # simulation setup
    nPart = 1000
    phantomStr = 'air_box'
    
    url_post_jobs = 'http://127.0.0.1:5000/v1/jobs'
    temp_dir = '/var/input_dicom/IDEAL-1_1dev/apiZip'
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
        
    # zip data into CT.zip, RP.zip, RD.zip and RS.zip (check if zip already exist)
    all_files = os.listdir(plan_dir)
    CT = get_and_zip_files('CT',all_files,plan_dir,temp_dir)
    RD = get_and_zip_files('RD',all_files,plan_dir,temp_dir)
    RS = get_and_zip_files('RS',all_files,plan_dir,temp_dir)
    RP = get_and_zip_files('RP',all_files,plan_dir,temp_dir)
    print(RP)
        
    # login to api
    login_data = {'account_login': 'myqaion', 'account_pwd': 'Password123'}
    r = requests.post('http://127.0.0.1:5000/v1/auth',headers = login_data)
    token = r.json()['authToken']
    
    # make post request to start api simulation
    args = {'username': 'myqaion',
            'configChecksum': '5b80f078f6d5c22e326ca310712aabaa0b1915e1',
            'numberOfParticles': nPart}

    with open(RP,'rb') as rp:
        with open(RD,'rb') as rd:
             with open(RS,'rb') as rs:
                with open(CT,'rb') as ct:
                     transfer_files = {"dicomRtPlan":rp,"dicomStructureSet":rs,"dicomCTs":ct,"dicomRDose":rd}
                     r = requests.post(url_post_jobs, files = transfer_files, data = args, headers={'Authorization': "Bearer " +token})
                                  
    # get output directory for simulation
    jobId = r.text
    outputdir = '/var/output/IDEAL-1_1release/'+jobId
    
    print(outputdir)
    
def get_and_zip_files(idString,all_files,plan_dir,destination):
    files = [f for f in all_files if f.startswith(idString)]
    if idString == 'RP':
        idString = files[0]
    filename = os.path.join(destination, idString + '.zip')
    zip_files(filename,files)
    return filename
    
def compress_data(zip_filename,files):
    for file in files:
        with ZipFile(zip_filename, "w") as zip_file:
            with open(file,'rb') as f:
                cont = f.read()
            zip_file.writestr(file, cont)
    return zip_file
    
if __name__ == '__main__':
    main()    
