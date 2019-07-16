import os
import sys

LOCAL_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_TESTS_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
LOCAL_ROOT_DIR = os.path.dirname(os.path.abspath(os.curdir))

sys.path.append(LOCAL_REPO_DIR)

from common import settings

# import all local/common modules


def check_the_logger():
    """ test the common setup logger function"""
    # Copy these lines into each script that needs a logger

    """------------------------------------------------------------------------------------------
    Standard Logging Configuration:
    ------------------------------------------------------------------------------------------"""

    LOCAL_LOG_DIR = os.path.join(LOCAL_REPO_DIR, os.path.join("logs", "logger"))
    logger = settings.setup_logger(**{"current_script":os.path.basename(__file__), "log_dir":LOCAL_LOG_DIR})
    """---------------------------------------------------------------------------------------"""
    
    # End Copy

    try:
        assert 0
    except Exception:
        logger.info("TEST INFO")

    try:
        assert 0
    except Exception:
        logger.error("TEST ERROR")

def check_config_variables(config):
    config_variables_list = [key.upper() for key in config.keys()]
    my_dir_var_name = ['DIRECTORY']
    my_db_var_name = ['DATABASE']

    for var_name in config_variables_list:
        if var_name in my_db_var_name:
            os.environ['DB_VAR_NAME'] = var_name
        elif var_name in my_dir_var_name:
            os.environ['DIR_VAR_NAME'] = var_name
        else:
            pass
    return

def check_project_directories(config):
    dir_config = settings.load_project_directory(config=config)
    all_dir_names = [key.upper() for key in dir_config.keys()]
    for dir_name in all_dir_names:
        check_dir = os.path.join(LOCAL_ROOT_DIR, os.environ[dir_name])
        try:
            assert os.path.isdir(check_dir)
        except Exception:
            raise Exception("Directory does not Exist {path}".format(path=check_dir))

    return

def check_database_support(config):
    my_db_type = 'POSTGRES'
    my_db_var_name = settings.load_db_var_name()
    db_config = config[my_db_var_name]

    try:
        sup_db_config = settings.check_database_supported(db_config=db_config, database_type=my_db_type)
        assert sup_db_config is not {}
    except Exception:
        raise Exception("Database type not found in config {db_type}".format(db_type=my_db_type))


def check_environment():
    settings.setup_environment()

def test_my_app_setup():
    check_the_logger()
    config = settings.get_config()
    check_config_variables(config=config)
    check_project_directories(config=config)
    check_database_support(config=config)
    check_environment()
