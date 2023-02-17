import configparser
import requests
import os
import zipfile
import hashlib
import time
from cryptography.fernet import Fernet

def transfer_files_to_server(outputdir,api_cfg):
    jobId = outputdir.split("/")[-1]
    tranfer_files = dict()
    monteCarloDoseDicom = None
    logFile = None
    for file in os.listdir(outputdir):
        # for now we pass only the dcm with the simulated full plan and the report .cfg
        if 'PLAN' in file and '.dcm' in file:
            monteCarloDoseDicom = file
        if '.cfg' in file:
            logFile = file
    if logFile is not None and monteCarloDoseDicom is not None:
        # first authenticate
        login_data = {'account_login': 'fava', 'account_pwd': 'Password456'} # TODO use login provided by myQA iON
        ra = requests.post(api_cfg['receiver']['url authentication'],headers = login_data)
        token = ra.json()['authToken']
        with open(os.path.join(outputdir,monteCarloDoseDicom),'rb') as f1:
            with open(os.path.join(outputdir,logFile),'rb') as f2:
                tranfer_files = {'monteCarloDoseDicom': f1,'logFile': f2}
                r = requests.post(os.path.join(api_cfg['receiver']['url to send result'],jobId), files=tranfer_files, headers={'Authorization': "Bearer " + token})
        
        return r
    else:
        return -1

def get_api_cfg(path):
    api_cfg = configparser.ConfigParser()
    with open(path,"r") as fp:
        api_cfg.read_file(fp)
    return api_cfg

def timestamp():
    return time.strftime("%Y_%m_%d_%H_%M_%S")

        
def unzip(dir_name):
    extension = ".zip"
    os.chdir(dir_name)
    for item in os.listdir(dir_name):
        if item.endswith(extension):
            file_name = os.path.abspath(item)
            zip_ref = zipfile.ZipFile(file_name) # create zipfile object
            zip_ref.extractall(dir_name)
            zip_ref.close()
            os.remove(file_name)

def read_ideal_job_status(cfg_settings):
    cfg = configparser.ConfigParser()
    cfg.read(cfg_settings)
    status = cfg['DEFAULT']['status']
    new_status = status
    if 'RUNNING GATE' in status:
        new_status = 'running'
    elif status == 'submitted' or 'PREPROCESSING' in status:
        new_status = 'submitting'
    elif 'POSTPROCESSING' in status and 'FAILED' not in status:
        new_status = 'postprocessing'
    elif status == 'FINISHED':
        new_status = 'finished'
    elif 'FAILED' in status:
        new_status = 'failed'
    if status == 'PREPROCESSING FINISHED, JOB QUEUED':
        new_status = 'waiting'
    
    return new_status

def generate_input_folder(input_dir,filename,username):
    rp = filename.split('.zip')[0]
    folders = [i for i in os.listdir(input_dir) if (username in i) and (rp in i)]
    index = len(folders)+1
    ID = username + '_' + str(index) + '_' + rp
    # create data dir for the job
    datadir = os.path.join(input_dir,ID)
    os.mkdir(datadir)
    
    return datadir, rp

def decrypt_login_dataframe(excel_path, key_path):
    # load key
    with open(key_path, 'rb') as mykey:
        key = mykey.read()
        
    # decript excel
    f = Fernet(key)
    with open(excel_path, 'rb') as encrypted_file:
        encrypted = encrypted_file.read()
    
    return f.decrypt(encrypted)

def sha1_directory_checksum(path):
    digest = hashlib.sha1()

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ['phantoms']]
        for names in files:
            file_path = os.path.join(root, names)

            # Hash the path and add to the digest to account for empty files/directories
            digest.update(hashlib.sha1(file_path[len(path):].encode()).digest())

            # Per @pt12lol - if the goal is uniqueness over repeatability, this is an alternative method using 'hash'
            # digest.update(str(hash(file_path[len(path):])).encode())

            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f_obj:
                    while True:
                        buf = f_obj.read(1024 * 1024)
                        if not buf:
                            break
                        digest.update(buf)

    return digest.hexdigest()

def check_username(sysconfig, username):
    ok = False
    if username in sysconfig['authorized users'].keys():
        ok = True
    return ok

def encrypt_file_with_key(filename='/home/fava/Desktop/api_accounts.xlsx',keyname='/home/fava/Desktop/login.key',enc_filename='/home/fava/Desktop/enc_api_accounts.xlsx'):
    key = Fernet.generate_key()
    with open(keyname, 'wb') as mykey:
        mykey.write(key)
    
    f = Fernet(key)
    
    with open('/home/fava/Desktop/api_accounts.xlsx', 'rb') as original_file:
        original = original_file.read()
    
    encrypted = f.encrypt(original)

    with open (enc_filename, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)