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
import pytz
import psycopg2
import psycopg2.extras
import psycopg2.extensions

LOCAL_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_SRC_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
LOCAL_LOG_DIR = os.path.join(LOCAL_REPO_DIR, os.path.join("logs", "logger"))

sys.path.append(LOCAL_REPO_DIR)

#pylint: disable=wrong-import-position
from common import settings
from common import basic_functions as cbf

# from source modules
from src import db_connections as dbconn
from src import file_wrangler
from src import sql_wrangler

#pylint: enable=wrong-import-position

# Standard Logging Configuration:
logger = settings.setup_logger(**{"current_script":os.path.basename(__file__), "log_dir":LOCAL_LOG_DIR})


"""------------------------------------------------------------------------------------
        File Functions
------------------------------------------------------------------------------------"""

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




"""------------------------------------------------------------------------------------
        SQL Functions
------------------------------------------------------------------------------------"""


# def sql_to_dict(db_class, qry, **kwargs):
#     """ INPUT: constructed query string with wild card %(variable)s to fill in with kwargs
#     RETURNS: values from database in dictionary"""
#     results = []

#     with db_class.connection as conn:
#         with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
#             sql = cursor.mogrify(qry, kwargs)
#             cursor.execute(sql)                
#             columns = [column[0] for column in cursor.description]
#             for row in cursor.fetchall():
#                 results.append(dict(zip(columns, row)))

#     return results

# def disconnect(db_class):
#     """ simple disconnect as per class method set to non __del__ """
#     if db_class is not None:
#         db_class = None
#     return



"""------------------------------------------------------------------------------------
        End SQL Functions
------------------------------------------------------------------------------------"""



"""------------------------------------------------------------------------------------
        ETL Functions
------------------------------------------------------------------------------------"""


# E: Extract
# Functions pertaining to downloading data from a database
def extract_from_database(db_class, table, schema):
    select_all_query = """SELECT * FROM {schema}.{table};""".format(schema=schema, table=table)
    results = sql_wrangler.sql_to_dict(db_class=db_class, qry=select_all_query)

    return results


# L: Load 
# Functions pertaining to uploading data to a database
def load_from_file(filename=None, extension=None, filepath=None):
    assert file_wrangler.file_check(filename=filename, extension=extension, filepath=filepath)
    file_data = cbf.load_file_to_dict(filename=filename, extension=extension, filepath=filepath)
    return file_data


"""------------------------------------------------------------------------------------
       End ETL Functions
------------------------------------------------------------------------------------"""
