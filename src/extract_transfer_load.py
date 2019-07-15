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
from common import basic_functions as cbf
from common import settings
#pylint: enable=wrong-import-position

# Standard Logging Configuration:
logger = settings.setup_logger(**{"current_script":os.path.basename(__file__), "log_dir":LOCAL_LOG_DIR})

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


class PostgresConnection:
    """ Class: for Postgres Connection: """
    def __init__(self, host, instance):
        """ config db in test/dev/prod mode """
        try:
            settings.load_environment()
            self.__host = host
            self.__port = os.environ['DB_PORT']
            self.user = os.environ['DB_USER']
            self.__secret_password = os.environ['DB_PASSWORD']
            self.db_name = instance

            self.connection = psycopg2.connect(
                                        host=self.__host,
                                        port=self.__port,
                                        user=self.user,
                                        password=self.__secret_password,
                                        dbname=self.db_name,
                                        connect_timeout=30
                                        #sslmode='verify-ca'
                                        #sslcert=[local path of client-cert.pem file] ~/.postgresql/postgresql.crt
                                        #sslkey=[local path of client-key.pem file] ~/.postgresql/postgresql.key
                                        #sslrootcert=[local path of server-ca.pem file] ~/.postgresql/root.crt
            )
            # db_logger.info("Postgres Connection to {0} Open".format(self.DBname))

            # TEST CONNECTION BY QUERYING SERVER VERSION RUNNING
            if not isinstance(self.connection.server_version, int):
                raise ValueError("Unable to Connect")

            logger.info("connected to database")
            self.connection.autocommit = True

        except ValueError as e:
            logger.error(e)

        except NameError as e:
            logger.error(e)

        except psycopg2.OperationalError as e:
            logger.error("Unable to connect!\n %(error)s ", error=e)

        except psycopg2.DatabaseError as e:
            logger.error(e)

    def __del__(self):
        self.connection.close()
        logger.info("disconnected from database")


"""------------------------------------------------------------------------------
FOR POSTGRES EXCEPTIONS
--------------------------------------------------------------------------------"""

def psycopg2_exceptions(func):
    """ EXCEPTIONS IN PSYCOPG2 Library"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """massive try block for all psycopg2 functions """ 
        results = None
        try:
            results = func(*args, **kwargs)

        #Subclasses of psycopg2.DatabaseError

        # Exception raised for errors that are due to problems with the 
        # processed data like division by zero, numeric value out of range, etc. 
        except psycopg2.DataError as e:
            logger.error("DataError: {error}".format(error=e))

        # Exception raised for errors that are related to the database’s operation and 
        # not necessarily under the control of the programmer, e.g. 
        # an unexpected disconnect occurs, the data source name is not found, 
        # a transaction could not be processed, a memory allocation error 
        # occurred during processing, etc.
        except psycopg2.OperationalError as e:
            logger.error("OperationalError: {error}".format(error=e))

        # Exception raised when the relational integrity of the database 
        # is affected, e.g. a foreign key check fails. 
        except psycopg2.IntegrityError as e:
            logger.error("IntegrityError: {error}".format(error=e))

        # Exception raised when the database encounters an internal error, 
        # e.g. the cursor is not valid anymore, the transaction is out of sync, etc. 
        except psycopg2.InternalError as e:
            logger.error("InternalError: {error}".format(error=e))        
        
        # Exception raised for programming errors, e.g. table not found or already exists, syntax 
        # error in the SQL statement, wrong number of parameters specified, etc.
        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError: {error}".format(error=e))

        #Exception raised in case a method or database API was used 
        # which is not supported by the database, e.g. requesting a rollback() 
        # on a connection that does not support transaction or has transactions turned off.
        except psycopg2.NotSupportedError as e:
            logger.error("NotSupportedError: {error}".format(error=e))


        # Subclasses of psycopg2.error (MORE GENERAL)

        # Exception raised for errors that are related to the 
        # database interface rather than the database itself. 
        except psycopg2.InterfaceError as e:
            logger.error("InterfaceError: {error}".format(error=e))

        #Exception raised for errors that are related to the database. 
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError: {error}".format(error=e))


        # MOST GENERAL
        except psycopg2.error as e:
            logger.error("GENERAL PSYCOPG2 ERROR: {error}".format(error=e))

        finally:
            return results

    return wrapped  

"""------------------------------------------------------------------------------
CURSOR as a WRAPPER
--------------------------------------------------------------------------------"""
def get_cursor(func):
    """
    Wrapper for opening cursor    

    COMMON METHOD to handle connection, auto-commit/rollback if error
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as curs:
            curs.execute(SQL)
    
    When a connection exits the with block, if no exception has been raised by the block, the transaction is committed. In case of exception the transaction is rolled back.

    When a cursor exits the with block it is closed, releasing any resource eventually associated with it. The state of the transaction is not affected.

    A connection can be used in more than a with statement and each with block is effectively wrapped in a separate transaction:
    
    """
    @wraps(func)
    @psycopg2_exceptions
    def wrapped(db_class, *args, **kwargs):
        """massive try block for all psycopg2 functions"""
        # db_class = PostgresConnection()
        with db_class.connection as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                results = func(cursor, *args, **kwargs)
                return results

        if connect is not None:
            connect = None
        
    return wrapped  


# E: Extract
# Functions pertaining to downloading data from a database
def extract_from_database(db_class, table, schema):
    select_all_query = """SELECT * FROM {schema}.{table};""".format(schema=schema, table=table)
    # quick_connect = PostgresConnection(host=host, instance=instance)

    with db_class.connection as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(select_all_query)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

    if db_class is not None:
        db_class = None
        
    return results


# L: Load 
# Functions pertaining to uploading data to a database
def load_from_file(filename=None, extension=None, filepath=None):
    assert file_check(filename=filename, extension=extension, filepath=filepath)
    file_data = cbf.load_file_to_dict(filename=filename, extension=extension, filepath=filepath)
    return file_data



@psycopg2_exceptions
def dict_to_sql(db_class, qry, **kwargs):
    """ INPUT: constructed query string with wild card %(variable)s to fill in with kwargs
    RETURNS: values from database in dictionary"""
    count = 0
    with db_class.connection as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            sql = cursor.mogrify(qry, kwargs)
            cursor.execute(sql)
            count = cursor.rowcount
    if db_class is not None:
        db_class = None

    return count


def insert_into_new(filedata, db_class, table, schema):
    """ Input data into empy table """
    total_row_count = len(filedata)
    row_success_count = 0
    count = 0
    unsuccessful_entries = list()
    for row in filedata:
        # weird fix
        try:
            row['id'] = row.pop('\ufeffid')
        except:
            pass 

        insert_columns = [key for key in row.keys()]
        insert_sql = insert_into_statement(table=table, schema=schema, columns=insert_columns)
        # if at first you try fail, try except fail again
        try:
            check_row_count = 0
            check_row_count = dict_to_sql(db_class=db_class, qry=insert_sql, **row)
            if not isinstance(check_row_count, int):
                check_row_count = 0

        except Exception as error:
            logger.info("Insert Failed")
            logger.error(error)
            check_row_count = 0
            unsuccessful_entries.append(row)

        row_success_count += check_row_count
        count += 1

        if count % 100 == 0:
            logger.info("PROGRESS: {suc} SUCCESS, {att} ATTEMPTS, {rem} REMAIN".format(att=count, suc=row_success_count, rem=(total_row_count-count)))

    return unsuccessful_entries


# CREATE
def insert_into_statement(table, schema, columns):
    """ 
    INSERT INTO: new data into existing table
    requires value wildcard string Mixed = False
    data_dict: all data to enter into table as dictionary
    """
    # Columns for SQL statement
    cols = ", ".join(columns)
    entry_wildcard = wildcard_fill(columns=columns, mixed=False)

    insert_sql = """INSERT INTO {schema}.{table} ({columns}) 
                    VALUES ({values});

                """.format(schema=schema, table=table, columns=cols, values=entry_wildcard)

    return insert_sql


def wildcard_fill(columns, mixed=None):
    """ Create wild card create for dict fill in later
    Use Mixed == True for SELECT and UPDATE queries
    Use Mixed == False for INSERT INTO queries
    ***POSSIBLY need to adjust for is NULL: Working 2019-06-05
    """  
    if mixed:
        wild = ", ".join(["{key} = %({var_val})s".format(key=col, var_val=col) for col in columns])
    else:
        wild = ", ".join(["%({})s".format(col) for col in columns])

    return wild

