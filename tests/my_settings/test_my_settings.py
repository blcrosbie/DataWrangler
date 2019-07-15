import os
import sys

LOCAL_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_TESTS_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
sys.path.append(LOCAL_REPO_DIR)

from common import settings

# import all local/common modules
def test_my_settings():
    check_the_logger()
    check_environment_variables()

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
        logger.info("Some info happened")

    try:
        assert 0
    except Exception:
        logger.error("Some error happened")

def check_environment_variables():
    settings.load_environment()

