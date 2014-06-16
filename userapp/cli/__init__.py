# Copyright 2012-2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
"""
USERAPP-CLI
----
A Universal Command Line Environment for UserApp.
"""

__version__ = '1.0.2'
__userapp_master_app_id__='51ded0be98035'

import os
import clidriver

def main():
	return clidriver.main()

if __name__ == '__main__':
	sys.exit(main())