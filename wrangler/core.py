import os
import duckdb
from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    """Abstract base class for all data generators."""
    def __init__(self, faker):
        self.fake = faker

    @abstractmethod
    def generate(self, num_rows):
        """Must return a dictionary of {filename: [list_of_dicts_data]}"""
        pass

class WranglerEngine:
    """Core engine to manage DuckDB connections and SQL execution."""
    def __init__(self, db_path='data_wrangler.db'):
        self.db_path = db_path
        self.con = duckdb.connect(self.db_path)

    def execute_script(self, script_path):
        if os.path.exists(script_path):
            with open(script_path, 'r') as f:
                self.con.execute(f.read())
        else:
            print(f"Warning: Script {script_path} not found.")

    def query(self, sql):
        return self.con.execute(sql).fetchall()

    def close(self):
        self.con.close()
