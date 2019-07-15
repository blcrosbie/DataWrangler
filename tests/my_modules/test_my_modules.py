import os
import sys
import json

LOCAL_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_TESTS_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
sys.path.append(LOCAL_REPO_DIR)

# import all local/common modules
from common import settings
from src import extract_transfer_load as etl


def test_all_my_modules():
    my_etl_functions()

def my_etl_functions():
    # Use a global backup directory for csv file ETL
    settings.load_environment()
    DATABASE_BACKUP_DIR = os.path.join(LOCAL_BASE_DIR, os.environ['DATABASE_BACKUP_DIR'])

    EXTRACT_DIR = os.path.join(DATABASE_BACKUP_DIR, os.path.join("ETL", "extract"))
    # LOAD_DIR = os.path.join(DATABASE_BACKUP_DIR, os.path.join("ETL", "load"))

    test_extension_list = ['.csv', '.json', '.txt', '.xml']
    for ext in test_extension_list:
        etl.is_extension_supported(extension=ext)

    test_fn = 'test_file'
    test_ext = '.csv'
    test_schema = 'archive'
    test_path = os.path.join(EXTRACT_DIR, test_schema)
    etl.file_check(filename=test_fn, extension=test_ext, filepath=test_path)
