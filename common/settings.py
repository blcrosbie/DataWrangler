#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thurs Jul 14 22:41:55 2019
@author: blcrosbie
"""
import os
import sys
import json
import datetime
import logging
import logging.config


def get_config():
    IMPORT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".config")
    IMPORT_CONFIG_FILE = os.path.join(IMPORT_CONFIG_DIR, "config.json")

    with open(IMPORT_CONFIG_FILE, 'r') as f:
        meta_import_config = json.load(f)

    project_config_filename = meta_import_config['PROJECT']['ENV_CONFIG_FILENAME']
    LOCAL_ENV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    project_details = os.path.join(LOCAL_ENV_DIR, project_config_filename)
    with open(project_details, 'r') as f:
        config = json.load(f)

    return config


def set_db_var_name(var_name):
    os.environ['DB_VAR_NAME'] = var_name

def set_dir_var_name(var_name):
    os.environ['DIR_VAR_NAME'] = var_name

def load_db_var_name():
    try:
        db_var_name = os.environ['DB_VAR_NAME']
    except:
        raise NameError("Database Environment Variables not set\n Run tests for my_connections with pytest")
    return db_var_name


def load_dir_var_name():
    try:
        dir_var_name = os.environ['DIR_VAR_NAME']
    except:
        raise NameError("Project Directory Environment Variables not set, Run tests for my_settings with pytest")

    return dir_var_name


def load_project_directory(config):
    my_dir_var_name = load_dir_var_name()
    dir_config = config[my_dir_var_name]

    all_dir_names = [key.upper() for key in dir_config.keys()]
    for dir_name in all_dir_names:
        os.environ[dir_name] = dir_config[dir_name]

    return dir_config


def check_database_supported(db_config, database_type):
    try:
        supported_db_config = db_config[database_type]
    except:
        raise NameError("{db_type} NOT SUPPORTED".format(db_type=database_type))

    return supported_db_config


def load_database_config(config, database_type):
    # Database Config only supports TO POSTGRES FOR NOW!
    my_db_var_name = load_db_var_name()
    db_config = config[my_db_var_name]
    sup_db_config = check_database_supported(db_config=db_config, database_type=database_type)

    all_db_fields = [key for key in sup_db_config.keys()]

    for db_field in all_db_fields:
        if 'USER' in db_field:
            os.environ['DB_USER'] = sup_db_config[db_field]
        elif 'PASSWORD' in db_field:
            os.environ['DB_PASSWORD'] = sup_db_config[db_field]
        elif 'PORT' in db_field:
            os.environ['DB_PORT'] = sup_db_config[db_field]
        elif 'HOST' in db_field:
            all_hosts = [key for key in sup_db_config[db_field].keys()]
            for db_host in all_hosts:
                if 'STAGING' in db_host:
                    os.environ['STAGING'] = sup_db_config[db_field][db_host]
                elif 'PRODUCTION' in db_host:
                    os.environ['PRODUCTION'] = sup_db_config[db_field][db_host]
                else:
                    pass
        elif 'DB' in db_field:
            all_instances = [key for key in sup_db_config[db_field].keys()]
            for db_instance in all_instances:
                if 'TEST' in db_instance:
                    os.environ['DB_TEST'] = sup_db_config[db_field][db_instance]
                elif 'DEV' in db_instance:
                    os.environ['DB_DEV'] = sup_db_config[db_field][db_instance]
                elif 'PROD' in db_instance:
                    os.environ['DB_PROD'] = sup_db_config[db_field][db_instance]
                else:
                    pass
        else:
            pass

    # # Credentials
    # os.environ['DB_USER'] = config['DATABASE']['POSTGRES']['POSTGRES_USER']
    # os.environ['DB_PASSWORD'] = config['DATABASE']['POSTGRES']['POSTGRES_PASSWORD']
    # os.environ['DB_PORT'] = config['DATABASE']['POSTGRES']['POSTGRES_PORT']
    # # Hosts
    # os.environ['STAGING'] = config['DATABASE']['POSTGRES']['POSTGRES_HOST']['STAGING']
    # os.environ['PRODUCTION'] = config['DATABASE']['POSTGRES']['POSTGRES_HOST']['PRODUCTION']
    # # Instances
    # os.environ['DB_TEST'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['TEST']
    # os.environ['DB_DEV'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['DEV']
    # os.environ['DB_PROD'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['PROD']

def setup_environment():
    my_config = get_config()
    my_dir_var_name = 'DIRECTORY'
    my_db_var_name = 'DATABASE'
    my_supported_db = 'POSTGRES'

    set_dir_var_name(var_name=my_dir_var_name)
    load_project_directory(config=my_config)

    set_db_var_name(var_name=my_db_var_name)
    load_database_config(config=my_config, database_type=my_supported_db)


def setup_logger(**kwargs):
    """ standardized logging module """

    for key, value in kwargs.items():
        if key == "current_script":
            current_script = str(value)
            current_script_fn = current_script.replace(".py", "")

        if key == "base_dir":
            base_dir = str(value)

        if key == "current_dir":
            current_dir = str(value)

        if key == "log_dir":
            LOG_DIR = str(value)

        # try to pass in a different level possible for other loggers
        if key == "level":
            level = value

    logging_config_path = os.path.dirname(os.path.abspath(__file__))
    log_config = os.path.join(logging_config_path, "logging.json")

    # os.chdir(logging_config_path)
    with open(log_config, 'rt') as file:
        config = json.load(file)
        temp_config = config
        # temp manipulate config for file storage setup
        #  default is "info.log" and "errors.log"
        old_info_fn = config["handlers"]["info_file_handler"]["filename"]
        old_errs_fn = config["handlers"]["error_file_handler"]["filename"]
        old_critical_fn = config["handlers"]["critical_file_handler"]["filename"]
        # not sure why DEBUG level not working, but all log entries post here
        old_all_fn = config["handlers"]["debug_file_handler"]["filename"] 
        try:
            info_fn = os.path.join(LOG_DIR, (current_script_fn + '_' + old_info_fn))
            errs_fn = os.path.join(LOG_DIR, (current_script_fn + '_' + old_errs_fn))
            critical_fn = os.path.join(LOG_DIR, (current_script_fn + '_' + old_critical_fn))
            all_fn = os.path.join(LOG_DIR, (current_script_fn+ '_' + old_all_fn))
        except NameError:
            info_fn = os.path.join(LOG_DIR, old_info_fn)
            errs_fn = os.path.join(LOG_DIR, old_errs_fn)
            critical_fn = os.path.join(LOG_DIR, old_critical_fn)
            all_fn = os.path.join(LOG_DIR, old_all_fn)
        finally:
            temp_config["handlers"]["info_file_handler"]["filename"] = info_fn
            temp_config["handlers"]["error_file_handler"]["filename"] = errs_fn
            temp_config["handlers"]["critical_file_handler"]["filename"] = critical_fn
            temp_config["handlers"]["debug_file_handler"]["filename"] = all_fn

    # os.chdir(current_dir)
    logging.config.dictConfig(temp_config)
    # except Exception as error:
    #   print("ERROR SETTING UP LOG: {error}".format(error=error))
    # finally:
    return logging.getLogger(current_script)
