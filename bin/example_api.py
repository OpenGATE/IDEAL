from ideal_module import * 
import os
from utils.condor_utils import zip_files
import requests
from zipfile import ZipFile


def main():
    # get rp folder

    plan_dir = '/var/data/IDEAL/io/IDEAL_ro/Commissioning/IR2Hc/1_IRPDs/120'

    os.chdir(plan_dir)
    
    # simulation setup
    nPart = 1000
    phantomStr = 'air_box'
    

    url_post_jobs = 'http://10.2.72.75:5000/v1/jobs'
    temp_dir = '/home/montecarlo/apiZip'

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

    r = requests.post('http://10.2.72.75:5000/v1/auth',headers = login_data)
    #r = requests.post('https://10.1.72.10:5000/v1/auth',headers = login_data,verify=False)

    token = r.json()['authToken']
    
    checksum_mamoc = 'b5b4154918dae327eaea30be7c81571a02aa8c93'#'5b80f078f6d5c22e326ca310712aabaa0b1915e1'
    checksum_mcc = '174c5e6254ba4af3351ddc02445a0f2b980ed1f6'
    # make post request to start api simulation
    args = {'username': 'myqaion',
            'configChecksum': checksum_mcc,
            'numberOfParticles': nPart}

    with open(RP,'rb') as rp:
        with open(RD,'rb') as rd:
             with open(RS,'rb') as rs:
                with open(CT,'rb') as ct:
                     transfer_files = {"dicomRtPlan":rp,"dicomStructureSet":rs,"dicomCTs":ct,"dicomRDose":rd}
                     r = requests.post(url_post_jobs, files = transfer_files, data = args,
                                       headers={'Authorization': "Bearer " +token},verify=False)
                                  
    # get output directory for simulation
    jobId = r.text
    outputdir = '/var/output/IDEAL-v1.1/'+jobId
    
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
