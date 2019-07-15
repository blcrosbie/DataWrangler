#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 25 20:26:41 2019

@author: blcrosbie
Basic Python Functions for Everyday Use
"""

import os
import csv
import json
import sys
import time
import datetime
from functools import wraps
import logging

"""--------------------------------------------------------------------------
    Data Type Enforcement Functions:
    functions that help keep Data Sanitized

--------------------------------------------------------------------------"""

def typecast(data, datatype):
    """ Can't find any function like this in python, for now manually set up
    data: some item you want to update the datatype
    datatype: string value for the type you want to cast
    ORIGINAL USE: Need to clean data from csv into postgres

    A Quick Lesson on Python Datatypes:

    bool: Boolean (true/false) types. Supported precisions: 8 (default) bits.

    int: Signed integer types. Supported precisions: 8, 16, 32 (default) and 64 bits.

    uint: Unsigned integer types. Supported precisions: 8, 16, 32 (default) and 64 bits.

    float: Floating point types. Supported precisions: 16, 32, 64 (default) bits and extended precision floating point (see note on floating point types).

    complex: Complex number types. Supported precisions: 64 (32+32), 128 (64+64, default) bits and extended precision complex (see note on floating point types).

    str: Raw string types. Supported precisions: 8-bit positive multiples.

    time: Data/time types. Supported precisions: 32 and 64 (default) bits.

    enum: Enumerated types. Precision depends on base type.

    """
    try:
        assert isinstance(datatype, str)

        if datatype == 'int' or datatype == 'integer':
            # ints are tricky, if it contains a '.' then you must first cast as float, then int
            casted = int(float(data))

        elif datatype == 'float':
            casted = float(data)

        elif datatype == 'str' or datatype == 'text' or datatype == 'character varying':
            casted = str(data)

        elif datatype == 'bool' or datatype == 'boolean':
            casted = bool(data)

        elif datatype == 'datetime':
            ### not sure what to do with this yet... ###
            casted = data

        # other datatypes to possible add in later, probably won't work as I hope for now
        elif datatype == 'tuple':
            casted = tuple(data)

        elif datatype == 'list':
            casted = list(data)

        elif datatype == 'dict':
            casted = dict(data)

        else:
            logging.error("{} don't know this datatype".format(datatype))
            casted = None

    except Exception as e:
        logging.error("{} don't know this datatype".format(datatype))
        logging.error(e)
    finally:
        return casted

def datatype_lookup(pg_db_data, pg_column_datatypes):
    """ Build the look up table for postgres:python datatype lookup """
    pg_to_py_dtype_lookup = dict()
    for key, val in pg_db_data.items():
        # logger.debug("\nColumn: {key}".format(key=key))
        if val is None:
            # logger.debug("entry blank")
            pass
        else:
            py_dtype = type(val).__name__
            logger.debug("Python dtype: {dtype}".format(dtype=py_dtype))
            logger.debug("Postgres dtype: {dtype}".format(dtype=pg_column_datatypes[key]))
            pg_to_py_dtype_lookup.update({pg_column_datatypes[key]:py_dtype})
    # logger.critical(pg_to_py_dtype_lookup)

    return pg_to_py_dtype_lookup

def sanitize_csv_data(csv_row_data, pg_column_datatypes, pg_to_py_dtype_lookup):
    """ need to clean the data, all strings from csv 
    NOT SURE WHERE THIS FUNCTION SHOULD LIVE YET"""
    clean_data = dict()
    for key, val in csv_row_data.items():
        pg_dtype = pg_column_datatypes[key]
        py_dtype = pg_to_py_dtype_lookup[pg_dtype]
        clean_val = typecast(val, py_dtype)
        clean_data.update({key:clean_val})

    return clean_data

def force_pg_sanitize(pg_column_datatypes, **kwargs):
    clean_data = dict()
    for key, val in kwargs.items():
        force_dtype = pg_column_datatypes[key]
        clean_data[key] = typecast(val, force_dtype)
    return clean_data



"""--------------------------------------------------------------------------
    DICTIONARY + JSON FUNCTIONS

--------------------------------------------------------------------------"""

def check_dictionary_depth(any_dict):
    """ diggin deep into dicts """
    # Start from the top, 0 deep
    max_depth, check = 0, 0

    # first step, check if input is actually a dict
    if isinstance(any_dict, dict):
        # it is! increment the depth counter by 1
        # now iterate through THIS dict, and see how deep it goes
        for key, check_val in any_dict.items():
            # for every val in this dict, run it from the top!
            check = check_dictionary_depth(check_val) + 1
            if check >= max_depth:
                max_depth = check   

        return max_depth

    # no longer have an instance of dict, return 0 if the item wasn't a dict at all to begin with
    else:
        return check

def remove_keys_from_dict(drop_key_list, multi_layer_dict):
    """ save some forlooping""" 
        # who cares, just make it a list of one


    if not isinstance(drop_key_list, list):
        drop_key_list = [drop_key_list]
    print("drop_key_list: {}".format(drop_key_list))

    depth = check_dictionary_depth(multi_layer_dict) 
    print(depth)
    if depth > 1:
        print("multi layer dict: \n")
        pretty_dictionary(multi_layer_dict)
        filtered_dict = {**multi_layer_dict}
        for key, val in multi_layer_dict.items():
            if isinstance(val, dict) and val != {}:
                pretty_dictionary(val)
                filtered_dict = remove_keys_from_dict(drop_key_list=drop_key_list, multi_layer_dict=val)
            elif not isinstance(val, dict) and key in drop_key_list:
                del filtered_dict[key]

            else:
                pass

        return filtered_dict

    elif depth == 1:
        filtered_dict = {**multi_layer_dict}
        for key, val in multi_layer_dict.items():
            if key not in drop_key_list:
                print(key)
                del filtered_dict[key]

        multi_layer_dict = {**filtered_dict}

    else:
        print(depth)
        print("end of the line")


    return multi_layer_dict

def my_json_defaults(unreadable_obj):
    if isinstance(unreadable_obj, (datetime.date, datetime.datetime)):
        readable_obj = str(unreadable_obj)
        # If I need to change it back remember the format used is datetime.datetime.isoformat()
        # OR ...
        # datetime_obj = datetime.datetime.strptime(readable_obj, '%Y-%m-%d %H:%M:%S.%f')
        return readable_obj



def pretty_dictionary(ugly_dictionary):
    """ Json dumps the ugly dict for a pretty dict ... typical Json"""
    print("------------------------------------------------------------------------")
    try:
        data_json = json.dumps(ugly_dictionary, indent=4, sort_keys=True, default=my_json_defaults)

        # if name is None:
        #     name = namestr(*ugly_dictionary)
        # print("""---------------------------- {name} ------------------------------------""".format(name=name))
        print(data_json)

    except Exception as e:
        # issue with the json crap 
        print(e)    
        print(ugly_dictionary)

    finally:
        print("------------------------------------------------------------------------")


def namestr(*args):
    for arg in args:
        return(arg)


def dict_list_drop_duplicates(dict_with_list):
    """ Needed to do this more than a few times
        Works for dict -> list of items"""
    try:
        assert isinstance(dict_with_list, dict)
        for top_key, item_list in dict_with_list.items():
            assert isinstance(item_list, list)
            unique_list = list()
            for row in item_list:
                if row not in unique_list:
                    unique_list.append(row)

            # "EXPLOIT" update function to get uniqueness
            dict_with_list.update({top_key:unique_list})

    except Exception as e:
        logging.critical(e)
        logging.info("Something Went Wrong in the duplicate drop dict function")

    finally:
        return dict_with_list

"""--------------------------------------------------------------------------
    File Handler Functions:
    functions that process files into the database

--------------------------------------------------------------------------"""

def detect_unique_keys(file_as_dict, tablename, number_of_pkeys=None):
    detected_unique_keys = list()
    dict_with_list = dict()
    scores = dict()
    total_rows = len(file_as_dict)
    time_stamps = ['created_at', 'updated_at']

    for row in file_as_dict:
        for key, val in row.items():
            if val != '' and key not in time_stamps:
                dict_with_list.setdefault(key, []).append(val)

    for key, list_val in dict_with_list.items():
        unique_val_count = len(list(dict.fromkeys(list_val)))
        unique_score = round(unique_val_count/len(list_val),2)
        complete_score = round(len(list_val)/total_rows,2)
        if number_of_pkeys == 1 and float(complete_score) == 1.0 and float(unique_score) == 1.0:
            detected_unique_keys.append(key)

        scores.update({key:unique_score})
        # complete_dict = dict(complete=complete_score)
        
        # scores.update({key:score_dict})

        logging.info("{key}: Uniqueness: {uniq_row}/{num_rows}={division}\t Completeness: {totals}".format(key=key, uniq_row=unique_val_count, num_rows=len(list_val), division=(unique_score), totals=complete_score))


    max_uniques = dict()
    score_max = {**scores}
    save_max_key_to_del = ''
    search_for_maxes = number_of_pkeys
    while search_for_maxes > 0:
        temp_max = max(score_max.values())
        for key, score in score_max.items():
            if score == temp_max:
                max_uniques.update({key:score})
                del scores[key]
                score_max = {**scores}
                save_max_key_to_del = key
            else:
                pass
           
        search_for_maxes -= 1
    detected_unique_keys = [key for key in max_uniques.keys()]

    return detected_unique_keys

def find_all_possible_fields(unstructured_list_of_dicts):
    all_fields = list()
    for element in unstructured_list_of_dicts:
        element_fields = [key for key in element.keys()]
        add_new_fields = list(set(element_fields) - set(all_fields))
        all_fields += add_new_fields

    return all_fields


def load_file_to_dict(filename, extension, filepath):
    """ version 3 from uploading csv files to psql
    Supports csv and json
    Current function with .txt works specifically with json-like files """

    fn = os.path.join(filepath,(filename + extension))
    if extension == '.csv':
        with open(fn, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            file_results = list()
            file_cols = reader.fieldnames
            for row in reader:
                file_results.append(json.loads(json.dumps(row)))

    elif extension == '.json':
        with open(fn, mode='r', encoding='utf-8') as f:
            reader = json.load(f)
            file_results = list()
            for row in reader:
                file_results.append(row)

    else:
        logging.error("{ext} not supported yet".format(ext=extension))

    return file_results


"""--------------------------------------------------------------------------
    TESTING AND DEBUGGING FUNCTIONS

--------------------------------------------------------------------------"""

def function_timer(func):
    """ for query optimization and code performance """
    @wraps(func)
    def wrapped(*args, **kwargs):
        """ wrapped function, below time is calculated to (hr):(min):(sec).(ms) """
        start = time.time()
        func(*args, **kwargs)
        stop = time.time()
        time_to_do_func = stop - start
        # convert to time readable format
        convert_hr = int(time_to_do_func / 3600)
        convert_min = int((time_to_do_func - convert_hr) / 60)
        convert_sec = round((time_to_do_func - convert_hr*3600 - convert_min*60), 3)
        watch = "{0}:{1}:{2}".format(convert_hr, convert_min, convert_sec)
        logging.info("run time : {look_at}\n".format(look_at=watch))
    return wrapped

def investigate_error(func):
    """ USE FOR DEBUG ONLY, need to catch errors with less vague description"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """ wrapped, included pylint commentary for disable/enable """
        try:
            func(*args, **kwargs)

        #pylint: disable=broad-except
        except Exception as e:
            logging.error("GENERIC ERROR: {error}".format(error=e))
            sys.exit()
        #pylint: enable=broad-except
    return wrapped

def test_wrapper(func):
    """ the wrap to wrap all wraps """
    @wraps(func)
    @function_timer
    @investigate_error
    def test_wrapped(*args, **kwargs):
        logging.info("TEST: {name}".format(name=func.__name__))
        func(*args, **kwargs)
        logging.info("COMPLETED: {name}".format(name=func.__name__))
    return test_wrapped

def debug_start():
    print("------------------------------------------------------------------------")
    print("\t\t\t\tDEBUG START")
    print("------------------------------------------------------------------------")

def debug_stop():
    print("------------------------------------------------------------------------")
    print("\t\t\t\tDEBUG STOP")
    print("------------------------------------------------------------------------")
