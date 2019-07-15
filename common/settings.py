#!/usr/bin/env python3
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


def load_environment():
    IMPORT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".config")
    IMPORT_CONFIG_FILE = os.path.join(IMPORT_CONFIG_DIR, "config.json")

    with open(IMPORT_CONFIG_FILE, 'r') as f:
        meta_import_config = json.load(f)

    project_config_filename = meta_import_config['PROJECT']['ENV_CONFIG_FILENAME']
    LOCAL_ENV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    project_details = os.path.join(LOCAL_ENV_DIR, project_config_filename)
    with open(project_details, 'r') as f:
        config = json.load(f)

    os.environ['BASE_DIR'] = config['DIRECTORY']['BASE_DIR']
    os.environ['REPO_DIR'] = config['DIRECTORY']['REPO_DIR']
    os.environ['SRC_DIR'] = config['DIRECTORY']['SRC_DIR']
    os.environ['LOG_DIR'] = config['DIRECTORY']['LOG_DIR']
    os.environ['TEST_DIR'] = config['DIRECTORY']['TEST_DIR']
    os.environ['DATABASE_BACKUP_DIR'] = config['DIRECTORY']['DATABASE_BACKUP_DIR']

    # Database Config HARDCODED TO POSTGRES FOR NOW!
    # Credentials
    os.environ['DB_USER'] = config['DATABASE']['POSTGRES']['POSTGRES_USER']
    os.environ['DB_PASSWORD'] = config['DATABASE']['POSTGRES']['POSTGRES_PASSWORD']
    os.environ['DB_PORT'] = config['DATABASE']['POSTGRES']['POSTGRES_PORT']
    # Hosts
    os.environ['STAGING'] = config['DATABASE']['POSTGRES']['POSTGRES_HOST']['STAGING']
    os.environ['PRODUCTION'] = config['DATABASE']['POSTGRES']['POSTGRES_HOST']['PRODUCTION']
    # Instances
    os.environ['DB_TEST'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['TEST']
    os.environ['DB_DEV'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['DEV']
    os.environ['DB_PROD'] = config['DATABASE']['POSTGRES']['POSTGRES_DB']['PROD']






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
