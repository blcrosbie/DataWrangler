# DataWrangler
common File/Text/ETL functions for database use cases in python

# Integrate into your own database management project:
  To integrate into your own project, (temp fix since setup.py broken) create a directory for external github repositories like so:
  
  - ROOT_DIR/
    - --BASE_DIR/
    - ----SRC_DIR/
    - ----LOGS_DIR/
    - ----TESTS_DIR/
    - ----requirements.txt
    - ----setup.py
    - ----EXTERNAL_GITHUB_DIR/

  - ```$ cd <BASE_DIR>```
  - ```<BASE_DIR> $ mkdir <EXTERNAL_GITHUB_DIR> ```

  Embed Repository as Submodule
  - ```$ git submodule https://github.com/blcrosbie/DataWrangler external_github/DataWrangler```

# Run Tests:
  Automated Setup the Virtual Environment for backend testing
  - ```$ bash scripts/run_tests.sh```
   - Tests working for config, connectivity, and python logging