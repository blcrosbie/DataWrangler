#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thurs Jul 14 22:41:55 2019
@author: blcrosbie
"""
import os
import sys
import json


def load_environment():
    IMPORT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".config")
    IMPORT_CONFIG_FILE = os.path.join(IMPORT_CONFIG_DIR, "config.json")

    with open(IMPORT_CONFIG_FILE, 'r') as f:
        import_config = json.load(f)

    project_config_filename = import_config['PROJECT']['ENV_CONFIG_FILENAME']

    APP_ENV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    sys.path.append(APP_ENV_DIR)
    from setup_environment import setup_environment as setup_environment

    config = setup_environment(environment_directory=APP_ENV_DIR, config_filename=project_config_filename)

    os.environ['BASE_DIR'] = config['DIRECTORY']['BASE_DIR']
    os.environ['REPO_DIR'] = config['DIRECTORY']['REPO_DIR']
    os.environ['SRC_DIR'] = config['DIRECTORY']['SRC_DIR']
    os.environ['LOG_DIR'] = config['DIRECTORY']['LOG_DIR']
    os.environ['TEST_DIR'] = config['DIRECTORY']['TEST_DIR']
    os.environ['DATABASE_BACKUP_DIR'] = config['DIRECTORY']['DATABASE_BACKUP_DIR']



