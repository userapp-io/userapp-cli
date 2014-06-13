#!/usr/bin/env python
import sys

from setuptools import setup, find_packages

setup_options = dict(
    name='userapp-cli',
    version='1.0.0',
    description='Universal Command Line Environment for UserApp.',
    long_description=open('README.md').read(),
    author='Robin Orheden',
    author_email='robin.orheden@userapp.io',
    keywords='userapp cli',
    url='https://github.com/userapp-io/userapp-cli/',
    scripts=['bin/userapp'],
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