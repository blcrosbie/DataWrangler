import os
import sys
import json

LOCAL_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_TESTS_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
sys.path.append(LOCAL_REPO_DIR)

# import all local/common modules
from common import settings
from src import database_connection as cnx

def whats_my_db_type(config):
    """ Check all DB types that are in config and return list"""
    db_var_name = settings.load_db_var_name()
    db_config = config[db_var_name]
    all_db_types = [key.upper() for key in db_config.keys()]
    return all_db_types

def dummy_connect(db_type_list):
    """ check to see if Connection Class has been defined for each db_type in config"""
    for db_type in db_type_list:
        if db_type.upper() == 'POSTGRES':
            test_conn = cnx.PostgresConnection()
            test_conn = None
        else:
            raise NameError("{db} connection class not yet defined".format(db=db_type))


def my_database_functions():
    pass


def test_all_my_connections():
    settings.setup_environment()
    config = settings.get_config()
    my_db_types = whats_my_db_type(config=config)
    dummy_connect(db_type_list=my_db_types)
