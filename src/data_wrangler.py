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

# find base directory for file management and other configs
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
LOG_DIR = os.path.join(BASE_DIR, os.path.join("logs", "logger"))

# Use a global backup directory for csv file ETL
BACKUP_DIR = os.path.join(os.path.dirname(BASE_DIR), "database_backup")
EXTRACT_DIR = os.path.join(BACKUP_DIR, os.path.join("ETL", "extract"))
LOAD_DIR = os.path.join(BACKUP_DIR, os.path.join("ETL", "load"))

#pylint: disable=wrong-import-position
sys.path.append(BASE_DIR)
# To import my local modules

from setup import setup_logger as setup_logger
from my_modules import extract_transfer_load as etl

# End import my local modules
sys.path.append(SRC_DIR)
#pylint: enable=wrong-import-position

# Standard Logging Configuration:
logger = setup_logger.get_logger(**{"current_script":os.path.basename(__file__), "base_dir":BASE_DIR, "log_dir":LOG_DIR})

def main():
    """ Main: manual enter filename info """
    fn_to_load = 'test_file'
    ext = '.csv'
    schema = 'archive'
    fn_to_load_path = os.path.join(EXTRACT_DIR, schema)
    etl.load_from_file(filename=fn_to_load, extension=ext, filepath=fn_to_load_path)


if __name__ == '__main__':
    main()