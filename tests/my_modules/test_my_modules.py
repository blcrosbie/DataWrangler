import os
import sys
import json
import datetime

# import all local/common modules

# TESTS_MY_MODULES_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(TESTS_DIR)
sys.path.append(BASE_DIR)

# Use a global backup directory for csv file ETL
BACKUP_DIR = os.path.join(os.path.dirname(BASE_DIR), "database_backup")
EXTRACT_DIR = os.path.join(BACKUP_DIR, os.path.join("ETL", "extract"))
LOAD_DIR = os.path.join(BACKUP_DIR, os.path.join("ETL", "load"))

def test_all_my_modules():
	my_etl_functions()

def my_etl_functions():
	from src import extract_transfer_load as etl
	test_extension_list = ['.csv', '.json', '.txt', '.xml']
	for ext in test_extension_list:
		etl.is_extension_supported(extension=ext)

	test_fn = 'test_file'
	test_ext = '.csv'
	test_schema = 'archive'
	test_path = os.path.join(EXTRACT_DIR, test_schema)
	etl.file_check(filename=test_fn, extension=test_ext, filepath=test_path)
