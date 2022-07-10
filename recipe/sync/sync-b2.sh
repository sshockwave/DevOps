#!/bin/bash
set -e

# suppose that MONITOR_URL is defined

# Paths
cd "$( dirname -- "$0"; )"
PATH_USR="/volume1/usr"
PATH_DEV="/volume1/dev"
PATH_LOG="/volume1/log"
PATH_ENC="/volume1/enc"
LOCK_FILE="/tmp/rclone.lock" # No spaces!
LOG_PATH="${PATH_LOG}/rclone"
PASS_FILE="${PATH_ENC}/career/storage/20201212-rclone/htpasswd"

curl -m 10 --retry 5 ${MONITOR_URL}/start

# One instance only
# https://stackoverflow.com/questions/185451/quick-and-dirty-way-to-ensure-only-one-instance-of-a-shell-script-is-running-at
if [ -e ${LOCK_FILE} ] && kill -0 $(cat ${LOCK_FILE}); then
	echo "already running"
	exit
fi
echo $$ > ${LOCK_FILE}

TZ="Asia/Shanghai"
LOG_MON="$(TZ=$TZ date '+%Y-%m')"
LOG_TIME="$(TZ=$TZ date '+%Y%m%d-%H%M%S')"
INFO_FILE="${LOG_PATH}/info/${LOG_MON}/${LOG_TIME}.log"
ERROR_FILE="${LOG_PATH}/${LOG_TIME}.err"
BACKUP_PATH="${PATH_DEV}/inbound/backup/${LOG_TIME}"
RC_FLAGS=(
	--filter-from syno-filters.txt
	--log-level INFO
	--log-file "${INFO_FILE}"
	--stats 0
	--rc
	--rc-web-gui
	--rc-web-gui-no-open-browser
	--rc-htpasswd=${PASS_FILE}
#	--track-renames
#	--track-renames-strategy modtime,leaf,size
	--fast-list
)

function clean_up ()
{
	code=$?
	rm -f ${LOCK_FILE}
	curl -m 10 --retry 5 ${MONITOR_URL}/$code
	if [ $code == 0 ]
	then exit 0
	fi
	echo "[Bash Script] Command exited with code $code" >> "${INFO_FILE}"
	if ! grep ERROR -i "${INFO_FILE}" > "${ERROR_FILE}"
	then rm "${ERROR_FILE}"
	fi
	exit $code
}
trap clean_up EXIT

mkdir -p "$(dirname "$INFO_FILE")"

source /volume1/var/miniconda3/bin/activate

# File transfers
#./rclone copy rsHemi:rsHemi/dev/rsdanvers ${PATH_DEV}/inbound --backup-dir=${BACKUP_PATH} ${RC_FLAGS[@]}

# Merge into /usr
#./rclone copy esHemi:/dev/merge/usr ${PATH_USR} --backup-dir=${BACKUP_PATH} ${RC_FLAGS[@]}
#./rclone move rsHemi:rsHemi/dev/merge/usr rsHemi:rsHemi/usr ${RC_FLAGS[@]}

# Sync to cloud
rclone sync ${PATH_ENC} ecHemi: ${RC_FLAGS[@]}
rclone sync ${PATH_USR} esHemi:usr/ ${RC_FLAGS[@]}
