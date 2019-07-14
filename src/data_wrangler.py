#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 10:32:22 2019
@author: blcrosbie

Common Extract/Transfer/Load functions for Postgres Database
"""

import os
import sys
import json
import time
import datetime
from functools import wraps

def is_extension_supported(extension):
    """ MANUAL UPDATES REQUIRED IN THIS CHECK
    Work on Extending the Features of ETL start with CSV"""
    check_flag = False
    if extension == '.csv':
        check_flag = True
    elif extension == '.json':
        pass
    elif extension == '.txt':
        pass
    elif extension == '.xml':
        pass	
    else:
        pass

    return check_flag

def file_check(filename, extension, filepath):
    """ Basic built-in Existence CHECKS from os for filepath/filename+extension """
    # First check if the extension is supported within MY personal modules
    pass_flag = False
    if is_extension_supported(extension=extension):
        ext_check = True
    else:
        ext_check = False
        raise NameError("File Type {ext} not supported".format(ext=extension))

    # Next check if this filepath is valid
    if os.path.isdir(filepath):
        path_check = True
    else:
        path_chech = False
        raise FileNotFoundError("Directory does not Exist {path}".format(path=filepath))

    # Finally, put it all together and make sure this file exists
    full_filename = os.path.join(filepath, filename+extension)
    if os.path.isfile(full_filename):
        file_check = True
        pass_flag = True
    else:
        file_check = False
        raise FileNotFoundError("File does not Exist {fn}".format(fn=filename))

    assert ext_check
    assert path_check
    assert file_check

    return pass_flag


# E: Extract
# Functions pertaining to downloading data from a database
def extract_from_database(filename=None, extension=None, filepath=None):
    assert file_check(filename=filename, extension=extension, filepath=filepath)
	

# L: Load 
# Functions pertaining to uploading data to a database
def load_from_file(filename=None, extension=None, filepath=None):
    assert file_check(filename=filename, extension=extension, filepath=filepath)




