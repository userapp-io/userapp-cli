#!/usr/bin/env python
import os, sys

from userapp.cli import __version__
from setuptools import setup, find_packages

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup_options = dict(
    name='userapp-cli',
    version=__version__,
    description='Universal Command Line Environment for UserApp.',
    long_description=read_file('README.md'),
    author='Robin Orheden',
    author_email='robin.orheden@userapp.io',
    keywords='userapp cli',
    url='https://github.com/userapp-io/userapp-cli/',
    scripts=['bin/userapp'],
    zip_safe = False,
    namespace_packages = ['userapp'],
    packages=find_packages(exclude=['examples', 'tests']),
    install_requires=['setuptools', 'userapp', 'requests'],
    include_package_data=True,
    license="MIT",
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3'
    )
)

if 'py2exe' in sys.argv:
    import py2exe
    setup_options['console'] = ['bin/userapp']
    setup_options['options'] = {
        'py2exe': {
            'optimize': 0,
            'skip_archive': True,
            'packages': ['userapp', 'requests']
        }
    }

setup(**setup_options)