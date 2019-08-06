import os
import sys
import json

LOCAL_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_DIR = os.path.dirname(LOCAL_TESTS_DIR)
LOCAL_BASE_DIR = os.path.dirname(LOCAL_REPO_DIR)
LOCAL_HOME_DIR = os.path.expanduser("~")
sys.path.append(LOCAL_REPO_DIR)

# import all local/common modules
from common import settings
from src import extract_transfer_load as etl
from src import file_wrangler
from src import sql_wrangler


def test_all_my_modules():
    my_etl_functions()

def my_etl_functions():
    # Use a global backup directory for csv file ETL
    settings.setup_environment()
    DATABASE_BACKUP_DIR = os.path.join(LOCAL_HOME_DIR, os.environ['DATABASE_BACKUP_DIR'])
    EXTRACT_DIR = os.path.join(DATABASE_BACKUP_DIR, os.path.join("ETL", "extract"))
    # LOAD_DIR = os.path.join(DATABASE_BACKUP_DIR, os.path.join("ETL", "load"))

    test_extension_list = ['.csv', '.json', '.txt', '.xml']
    for ext in test_extension_list:
        file_wrangler.is_extension_supported(extension=ext)

    test_fn = 'test_file'
    test_ext = '.csv'
    test_schema = 'archive'
    test_path = os.path.join(EXTRACT_DIR, test_schema)
    file_wrangler.file_check(filename=test_fn, extension=test_ext, filepath=test_path)
