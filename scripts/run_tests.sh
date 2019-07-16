#!/bin/sh

# Ensure working in REPO directory
BASE_DIR=$PWD
cd $BASE_DIR
echo "$PWD"

# Set log directories
COMMIT_TIMESTAMP=`date +'%Y-%m-%d %H:%M:%S %Z'`
DATELOG=`date +'%Y-%m-%d-%H-%M-%S'`
# LOG=${REPO}'/logs/unittests/'${DATELOG}'.txt'
PIP_LOG=${BASE_DIR}'/logs/unittests/'${DATELOG}'_pipvenv.txt'
PYTESTS_LOG=${BASE_DIR}'/logs/unittests/'${DATELOG}'_pytests.txt'
SETUP_LOG=${BASE_DIR}'/logs/unittests/'${DATELOG}'_setup.txt'

# Detect OS
OS="`uname`"
case $OS in
  'Linux')
    OS='Linux'
    alias ls='ls --color=auto'
    ;;
  'FreeBSD')
    OS='FreeBSD'
    alias ls='ls -G'
    ;;
  'WindowsNT')
    OS='Windows'
    ;;
  'Darwin') 
    OS='Mac'
    ;;
  'SunOS')
    OS='Solaris'
    ;;
  'AIX') ;;
  *) ;;
esac

# Setup Virtual ENV and run tests
if [[ $OS == 'Mac' ]]; then
  echo "Running on Mac"
  python3 -m pip install --user virtualenv >> ${PIP_LOG}
  python3 -m virtualenv .my_test_venv >> ${PIP_LOG}
  source .my_test_venv/bin/activate
  pip install -r requirements.txt >> ${PIP_LOG}
  python3 setup.py install >> ${SETUP_LOG}
  pytest -v  >> ${PYTESTS_LOG}

  # Tear Down
  echo "Party's over, shut down the venv"
  deactivate
  rm -r .my_test_venv


elif [[ $OS == 'Linux' ]]; then
  echo "Running on Linux"
  python3 -m pip install --user virtualenv >> ${PIP_LOG}
  python3 -m venv .my_test_venv >> ${PIP_LOG}
  source .my_test_venv/bin/activate
  pip install -r requirements.txt >> ${PIP_LOG}
  python3 setup.py install >> ${SETUP_LOG}
  pytest -v >> ${PYTESTS_LOG}

  # Tear Down
  echo "Party's over, shut down the venv"
  deactivate
  rm -r .my_test_venv

elif [[ $OS == 'Windows' ]]; then
  echo "Running on Windows"
  python get-pip.py >> ${PIP_LOG}
  pip install virtualenv >> ${PIP_LOG}
  virtualenv .my_test_env
  .\.my_test_env\Scripts\activate.bat
  pip install -r requirements.txt >> ${PIP_LOG}
  python setup.py install >> ${SETUP_LOG}
  pytest -v  >> ${PYTESTS_LOG}

  # Tear Down
  echo "Party's over, shut down the venv"
  deactivate
  rm -r .my_test_venv

else
  echo "Not Running"

fi



