#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thurs Jun 21 18:14:07 2019

@author: blcrosbie
Standard Modules
"""
import os
import sys
import csv
import json
import datetime
import logging
import logging.config


def get_logger(env_key=None, **kwargs):
    """ standardized logging module """
    if env_key is None:
        env_key = "LOG_CFG"
    #value = os.getenv(env_key, None)
    # if value:
    #   path = value

    # if level is None:
    #   level = logging.INFO

    logging_config_path = os.path.dirname(os.path.abspath(__file__))
    log_config = os.path.join(logging_config_path, "logging.json")

    for key, value in kwargs.items():
        if key == "current_script":
            current_script = str(value)
            current_script_fn = current_script.replace(".py", "")
        if key == "base_dir":
            BASE_DIR = str(value)

        if key == "log_dir":
            LOG_DIR = str(value)

        # try to pass in a different level possible for other loggers
        if key == "level":
            level = value

    os.chdir(logging_config_path)
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

    os.chdir(BASE_DIR)
    logging.config.dictConfig(temp_config)
    # except Exception as error:
    #   print("ERROR SETTING UP LOG: {error}".format(error=error))
    # finally:
    return logging.getLogger(current_script)
