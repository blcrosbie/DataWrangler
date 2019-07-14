import os
import sys

# import all local/common modules

# TESTS_SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(TESTS_DIR)

def test_my_setup():
	setup_the_logger()

def setup_the_logger():
    """ test the common setup logger function"""
    # Copy these lines into each script that needs a logger

    """------------------------------------------------------------------------------------------
    Standard Logging Configuration:
    ------------------------------------------------------------------------------------------"""
    sys.path.append(BASE_DIR)
    from setup import setup_logger as setup_logger
    LOG_DIR = os.path.join(BASE_DIR, os.path.join("logs", "logger"))
    logger = setup_logger.get_logger(**{"current_script":os.path.basename(__file__), "base_dir":BASE_DIR, "log_dir":LOG_DIR})
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