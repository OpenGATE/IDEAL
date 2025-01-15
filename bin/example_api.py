import os
from utils.condor_utils import zip_files
import requests
from zipfile import ZipFile


def main():
    # get rp folder
    base_dir ='home'
    plan_dir = f'/{base_dir}/ideal/0_Data/02_ref_RTPlans/IR2HBLc/01_IDDs/ISD0cm/E120.0MeV/'
    os.chdir(plan_dir)
    
    # simulation setup
    nPart = 1000
    phantomStr = 'air_box'
    ip_port = '10.2.72.75:5000'
    url_post_jobs = f'http://{ip_port}/v1/jobs' #'http://10.2.72.75:5000/v1/jobs'
    temp_dir = f'/{base_dir}/fava/Desktop/apiZip'
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
    login_data = {'account-login': 'myqaion', 'account-pwd': 'Password123'}
    #r = requests.post('http://10.2.72.75:5000/v1/auth',headers = login_data)
    r = requests.post(f'http://{ip_port}/v1/auth',headers = login_data)
    token = r.json()['authToken']
    
    checksum_mamoc = '086bc516b6c3ab887a998aaf6bc511675a36f970'
    #checksum_mcc = '174c5e6254ba4af3351ddc02445a0f2b980ed1f6'
    # make post request to start api simulation
    args = {'username': 'myqaion',
            'configChecksum': checksum_mamoc,
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
