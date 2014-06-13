#!/bin/bash

if [ "$(id -u)" != "0" ]; then
	echo "Installation requires root."
	exit 1
fi

BIN_PATH="/usr/local/bin/userapp"
CONFIG_DIR_PATH="/etc/userapp"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pip install userapp > /dev/null

cp $SCRIPT_DIR/src/userapp-cli.py $BIN_PATH
chmod +x $BIN_PATH

if [ ! -d $CONFIG_DIR_PATH ] ; then
	mkdir $CONFIG_DIR_PATH
	touch $CONFIG_DIR_PATH/config.json
fi

chmod -R 777 $CONFIG_DIR_PATH

echo "Installed successfully. Usage: userapp help"