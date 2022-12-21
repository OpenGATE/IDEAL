import configparser
import requests
import os

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
        with open(os.path.join(outputdir,monteCarloDoseDicom),'rb') as f1:
            with open(os.path.join(outputdir,logFile),'rb') as f2:
                tranfer_files = {'monteCarloDoseDicom': f1,'logFile': f2}
                r = requests.post(os.path.join(api_cfg['receiver']['url to send result'],jobId), files=tranfer_files)
#        tranfer_files = {'monteCarloDoseDicom': open(os.path.join(outputdir,monteCarloDoseDicom),'rb'), 'logFile': open(os.path.join(outputdir,logFile),'rb')}
#        r = requests.post(api_cfg['receiver']['url to send result']+"/"+jobId, files=tranfer_files)
        
        return r
    else:
        return -1

def get_api_cfg(path):
    api_cfg = configparser.ConfigParser()
    with open(path,"r") as fp:
        api_cfg.read_file(fp)
    return api_cfg
