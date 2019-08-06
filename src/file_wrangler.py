#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 10:32:22 2019
@author: blcrosbie

Common Extract/Transfer/Load functions for Postgres Database
Using SQL wrangler module (sql_wrangler.py)
Using Database Class Declarations module (db_connections.py)
"""

import os
import sys
import json
import time
import datetime
from functools import wraps


"""------------------------------------------------------------------------------------
        File Functions
------------------------------------------------------------------------------------"""

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

def is_database_supported(database_type):
    """ MANUAL UPDATES REQUIRED IN THIS CHECK
    Work on Extending the Features of ETL start with CSV"""
    check_flag = False
    if database_type.lower() == 'postgres':
        check_flag = True
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
        path_check = False
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

def compare_sources(filedata, dbdata):
    """ for information about file to load into database"""
    num_rows_file = len(filedata)
    num_rows_db = len(dbdata)

    for file_row in filedata:
        for fkey, fval in file_row.items():
            if fval == '':
                file_row[fkey] = None
            elif fval == 't' or fval == 'TRUE':
                file_row[fkey] = True
            elif fval == 'f' or fval == 'FALSE':
                file_row[fkey] = False
            elif fkey == 'updated_at' or fkey == 'created_at':
                if len(fval) < 29:
                    # Fix the Flippin' Trailin' Zeds Guy!
                    num_trailing_zeros = 29 - len(fval)
                    tz_split = fval.split('+')
                    add_zeros_here = tz_split[0]
                    add_tz_back = tz_split[1]
                    for zed in range(0, num_trailing_zeros):
                        add_zeros_here = add_zeros_here + '0'
                    add_zeros_here = add_zeros_here + '+' + add_tz_back

                    file_row[fkey] = str(add_zeros_here)
                    #new_time = datetime.datetime.strptime(fval, '%Y-%m-%d %H:%M:%S.%f+00')
            else:
                pass

    for db_row in dbdata:
        for dbkey, dbval in db_row.items():
            try:
                assert isinstance(dbval, (datetime.date, datetime.datetime))
                # str_time = str(dbval)
                csv_time = datetime.datetime.strftime(db_row[dbkey], '%Y-%m-%d %H:%M:%S.%f%Z')
                db_row[dbkey] = str(csv_time)
            except:
                pass

    same_data = list()
    fresh_data = list()

    # Compare File against DB Table
    for file_row in filedata:
        # to speed up search, update a "check dict" which will get shorter for every "match"
        found_match = False
        db_check = dbdata
        for db_row in db_check:
            if file_row == db_row:
                same_data.append(db_row)
                dbdata.remove(db_row)
                found_match = True
        if not found_match:
            fresh_data.append(file_row)

    num_same = len(same_data)
    num_diff = len(fresh_data)
    assert (num_same + num_diff) == len(filedata)
    logger.info("{num_rows} rows in file".format(num_rows=num_rows_file))
    logger.info("{num_rows} total rows in DB".format(num_rows=num_rows_db))
    logger.info("{same} matching rows in DB".format(same=num_same))

    return fresh_data

"""------------------------------------------------------------------------------------
        End File Functions
------------------------------------------------------------------------------------"""
