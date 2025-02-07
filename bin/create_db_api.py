#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 08:37:30 2024

@author: fava
"""

from apiflask import APIFlask
from flask_sqlalchemy import SQLAlchemy
import utils.api_utils as ap 
import ideal_module as idm
from utils.api_schemas import define_user_model, define_server_credentials_model
import os
import configparser

# Initialize sytem configuration once for all
sysconfig = idm.initialize_sysconfig(username = 'myqaion')
base_dir = sysconfig['IDEAL home']
input_dir = sysconfig["input dicom"]
log_dir = sysconfig['logging']
daemon_cfg = os.path.join(base_dir,'cfg/log_daemon.cfg')
sysconfig_path = os.path.join(base_dir,'cfg/system.cfg')
log_parser = configparser.ConfigParser()
log_parser.read(daemon_cfg)
ideal_history_cfg = log_parser['Paths']['cfg_log_file']
api_cfg = ap.get_api_cfg(log_parser['Paths']['api_cfg'])
commissioning_dir = sysconfig['commissioning']

app = APIFlask(__name__,title='IDEAL interface', version='1.0')

# api configuration
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + api_cfg['server']['credentials db']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
host_IP = api_cfg['server']['IP host']


# register database 
db = SQLAlchemy(app)

User = define_user_model(db) 
Server = define_server_credentials_model(db)

# initialize database
with app.app_context():
    db.create_all()
    # user: credential of the IDEAL users
    user = User('username','password','Name','Surname','clinical')
    # server: credentials used by IDEAL internally to access the client and return the simulations results
    server = Server('admin','admin_pwd')
    db.session.add(user)
    db.session.add(server)
    db.session.commit()