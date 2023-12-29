import unittest
import configparser
import os
from utils.condor_utils import *
from bin.log_daemon import *
		
class TestShellOutputRet(unittest.TestCase):
	
	def test_returned_value(self):
		ret, out = shell_output_ret("ls")
		self.assertEqual(ret, 0)
		ret, out = shell_output_ret("lsa")
		self.assertFalse(ret == 0)
		
class TestShellOutput(unittest.TestCase):
    
    def test_basic_function(self):
        out = shell_output("ls")
        self.assertIsNotNone(out)

class TestGetPids(unittest.TestCase):
    
    def test_input(self):
        with self.assertRaises(TypeError):
            pids = get_pids(3)
            
    def test_basic_function(self):
        this_script = os.path.basename(__file__)
        pids = get_pids(this_script)
        print("\npids: ",pids)
        self.assertTrue(bool(pids))

class TestGetDaemons(unittest.TestCase):

    def test_input(self):
        with self.assertRaises(AssertionError):
            # function must be called only with the name of the job control daemon script
            daemons = get_job_daemons("python") 
            
    def test_basic_function(self):
        daemons = get_job_daemons("job_control_daemon.py")
        print(daemons)

class TestGetJobs(unittest.TestCase):

    def test_basic_function(self):
        status = get_jobs_status()
        print(status)
        
class TestUpdateJobStatus(unittest.TestCase):
    
    def setUp(self):
        cfg_parser = configparser.ConfigParser()
        cfg_parser.read("/opt/IDEAL-1.1test/cfg/log_daemon.cfg")
        self.manager = log_manager(cfg_parser)
        self.stati = self.manager.job_status_dict
        self.all_jobs = {'800': {'IDs':'0-11', 'RUN':'_', 'DONE':'_', 'IDLE':'_', 'HOLD':'_'}}
        self.parser_sec ={'Submission date':'2022-09-19 08:12:57','Work_dir':'/work','Submission settings':'/settings',
                          'Status':'','Condor id':'800','Condor status':'','Job control daemon':''}
        
    def tearDown(self):
        self.all_jobs.clear()
        self.parser_sec.clear()
        
    def test_job_in_queue(self):
        self.manager.update_job_status(self.parser_sec,self.all_jobs)
        job_id = self.parser_sec['Condor id']
        self.assertEqual(self.parser_sec['Condor status'],str(self.all_jobs[job_id]))
        
    def test_job_finished(self):
        self.parser_sec['Condor id']='810' #job not in the queue
        self.parser_sec['Status']='FINISHED'
        self.manager.update_job_status(self.parser_sec,self.all_jobs)
        self.assertEqual(self.parser_sec['Condor status'],self.stati['done'])
        
    def test_job_status_uncertain(self):
        self.parser_sec['Condor id']='810' #job not in the queue
        self.manager.update_job_status(self.parser_sec,self.all_jobs)
        self.assertEqual(self.parser_sec['Condor status'],self.stati['checking'])
        self.assertIn('Last checked',self.parser_sec)
            
    def test_job_unsuccessfull(self):
        self.parser_sec['Condor id']='810' #job not in the queue
        self.parser_sec['Last checked'] = '2022-09-15 08:12:57'  # old enought to be considered stabilized
        self.parser_sec['Condor status'] = self.stati['checking'] 
        self.manager.update_job_status(self.parser_sec,self.all_jobs)
        self.assertEqual(self.parser_sec['Condor status'],self.stati['unsuccessfull'])  

    @unittest.expectedFailure
    def test_unexpected_behaviour(self):
        self.parser_sec['Condor id']='810' #job not in the queue
        self.parser_sec['Condor status'] = self.stati['unsuccessfull']
        self.manager.update_job_status(self.parser_sec,self.all_jobs)
        # job status UNSUCCESSFULL should be a final state, not updated anymore
        # we perevent this by not calling this function if the status is already final
        # (Done by outer layer function)
        self.assertEqual(self.parser_sec['Condor status'],self.stati['unsuccessfull'])                                                           	

class TestDaemons(unittest.TestCase):
    
    def setUp(self):
        cfg_parser = configparser.ConfigParser()
        cfg_parser.read("/opt/IDEAL-1.1test/cfg/log_daemon.cfg")
        self.manager = log_manager(cfg_parser)
        
        # SETUP: 
        # w1 is a running instance of ideal with running daemon -> running job (=survives)
        # w2 is a running daemon not associated to any instance -> somehow we didn't create a section for this job and we lost track of it (=kill)
        # w3 is a completed instance with no daemon alive -> normal for job completed successfully (=nothing to do)
        # w4 is an instance with undefined condor status, with alive daemon -> e.g. job manually removed/postproc. error and daemon didn't stop (=wait untill end status is assigned)
        # w5 is a non completed instance, with no job running -> daemon had a problem (nothing to do here)
        # w6 is an unsuccessfully terminated instance, with running daemon -> kill
        
        self.daemons = {'/work1': '123456','/work2': '654321', '/work4': '109283', '/work6': '100000'}
        self.manager.parser = configparser.ConfigParser()
        self.manager.parser['0']={'Submission date':'2022-09-19 08:12:57','Work_dir':'/work1','Submission settings':'/settings1',
                          'Status':'','Condor id':'800','Condor status':'','Job control daemon':''}
        self.manager.parser['1']={'Submission date':'2022-09-19 09:12:57','Work_dir':'/work3','Submission settings':'/settings3',
                          'Status':'FINISHED','Condor id':'810','Condor status':'DONE','Job control daemon':''}
        self.manager.parser['2']={'Submission date':'2022-09-19 10:12:57','Work_dir':'/work4','Submission settings':'/settings4',
                      'Status':'DOSE POSTPROCESSING FAILED','Condor id':'820','Condor status':'BEING CHECKED','Job control daemon':''}
        self.manager.parser['3']={'Submission date':'2022-09-19 10:12:57','Work_dir':'/work5','Submission settings':'/settings5',
                      'Status':'GATE FAILED','Condor id':'830','Condor status':'BEING CHECKED','Job control daemon':''}
        self.manager.parser['4']={'Submission date':'2022-09-19 11:12:57','Work_dir':'/work6','Submission settings':'/settings6',
                      'Status':'DOSE POSTPROCESSING FAILED','Condor id':'840','Condor status':'UNSUCCESSFULL','Job control daemon':''}
        self.parser = self.manager.parser
        
    def test_update_daemon_status(self):
        for i in self.parser.sections():
            self.manager.update_job_daemon_status(self.parser[i],self.daemons)
        self.assertEqual(self.parser['0']['Job control daemon'],'Running with pid 123456')
        self.assertEqual(self.parser['1']['Job control daemon'],'Daemon successfully finished')
        self.assertEqual(self.parser['2']['Job control daemon'],'Running with pid 109283')
        self.assertEqual(self.parser['3']['Job control daemon'],'Daemon successfully finished')
        self.assertEqual(self.parser['4']['Job control daemon'],'Running with pid 100000')

        
    def test_untracked_daemons(self):
        a = self.manager.kill_untracked_daemons(self.daemons,test=True)
        self.assertNotIn('123456',a) #w1 survives
        self.assertIn('654321',a) #w2 dies

    def test_running_daemons(self):
        #Update status
        for i in self.parser.sections():
            self.manager.update_job_daemon_status(self.parser[i],self.daemons)
        pids = list()
        # kill daemons
        for i in self.parser.sections():
            pids.append(self.manager.kill_running_daemons(self.parser[i],test=True))
        self.assertNotIn('123456',pids) #w1 survives
        self.assertNotIn('109283',pids) # w4 survives for now
        self.assertIn('100000',pids) # w6 dies
        self.assertEqual(self.parser['4']['Job control daemon'],'Daemon killed')
        
        

        
        
        
