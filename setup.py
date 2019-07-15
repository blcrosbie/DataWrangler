import pip
import os

try:
	from setuptools import setup, Command
except ImportError:
	from disutils.core import setup


try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()

# class CleanCommand(Command):
#     """Custom clean command to tidy up the project root."""
#     user_options = []
#     def initialize_options(self):
#         pass
#     def finalize_options(self):
#         pass
#     def run(self):
#         os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')


# Test requirements
testing_setup_packages = ['pytest-runner']
testing_packages = ['pytest']

# my scripts for this backend
# to start: 1. filesize checks
# later: ADD one to create virtual environment + pip installs
my_scripts = ['scripts/filesize_checks.sh']


# App backend-repo version
version = '0.0.1'
my_app_name = 'src'
my_packages = [my_app_name]
my_github_url = 'https://github.com/blcrosbie/DataWrangler'

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

other_repo_links = []

install_requires = requirements + other_repo_links

dependency_links = []

setup(
	name=my_app_name,
	packages=my_packages,
	version=version,
	description='common File/Text/ETL functions for database use cases in python',
	url=my_github_url,
	dependency_links=dependency_links,
	author='blcrosbie',
	author_email='bcrosb31@gmail.com',
	long_description=long_description,
    install_requires=install_requires,
	setup_requires=testing_setup_packages,
	tests_require=testing_packages,
	scripts=my_scripts,
	# cmdclass={
 #        'clean': CleanCommand,
 #    },
	classifiers=[
        'Development Status :: Pilot',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: ETL',
        'Topic :: Database',
    ]

)