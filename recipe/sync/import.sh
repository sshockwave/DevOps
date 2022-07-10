#!/bin/bash

is_mounted() {
    mount | awk -v DIR="$1" '{if ($3 == DIR) {exit 0}} ENDFILE{exit -1}'
}

# Goto root
cd "$(dirname "$0")"/..

if [ $(hostname) == 'rsLake' ]
then
	PROFILE_DIR=/mnt/c/Users/sshockwave
	rs="python3 executable/rsync-annex.py"
	$rs "$PROFILE_DIR/Documents/WeChat Files/Backup/" backup/wechat/
	$rs "$PROFILE_DIR/OneDrive/lib/calibre" artwork/
	$rs "$PROFILE_DIR/AppData/Roaming/foobar2000/" backup/foobar/ --exclude 'running'
	git annex add .
	git commit
fi
