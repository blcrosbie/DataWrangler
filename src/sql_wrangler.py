#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 05 16:52:23 2019
@author: blcrosbie

Common Functions and statement manipulation with SQL and Python
"""

import os
import sys
import json
import time
import datetime
from functools import wraps
import psycopg2.extensions


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


@psycopg2_exceptions
def sql_to_dict(db_class, qry, **kwargs):
    """ INPUT: constructed query string with wild card %(variable)s to fill in with kwargs
    RETURNS: values from database in dictionary"""
    results = []

    with db_class.connection as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            sql = cursor.mogrify(qry, kwargs)
            cursor.execute(sql)                
            columns = [column[0] for column in cursor.description]
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

    return results

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
