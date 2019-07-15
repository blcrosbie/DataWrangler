#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 14:10:52 2019
@author: blcrosbie

DataWrangling data to and from the Database
"""

import os
import sys
import json
import time
import datetime
from functools import wraps

# find local base directory for my module import and project env setup
LOCAL_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_SRC_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
LOCAL_LOG_DIR = os.path.join(LOCAL_REPO_DIR, os.path.join("logs", "logger"))

#pylint: disable=wrong-import-position
sys.path.append(LOCAL_REPO_DIR)
# To import my local modules
from common import settings
from src import extract_transfer_load as etl
# End import my local modules

sys.path.append(LOCAL_SRC_DIR)
#pylint: enable=wrong-import-position

# Standard Logging Configuration:
logger = settings.setup_logger(**{"current_script":os.path.basename(__file__), "log_dir":LOCAL_LOG_DIR})

def main():
    """ Main: manual enter filename info """
    # run environment setup
    settings.load_environment()
    DATABASE_BACKUP_DIR = os.path.join(LOCAL_BASE_DIR, os.environ['DATABASE_BACKUP_DIR'])
    EXTRACT_DIR = os.path.join(DATABASE_BACKUP_DIR, os.path.join("ETL", "extract"))

    fn_to_load = 'test_file'
    ext = '.csv'
    schema = 'archive'
    fn_to_load_path = os.path.join(EXTRACT_DIR, schema)
    etl.load_from_file(filename=fn_to_load, extension=ext, filepath=fn_to_load_path)


if __name__ == '__main__':
    main()