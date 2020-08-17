#!/bin/bash

# beginning of the main flow
if [ "$#" -ne 1 ]; then
    echo "Usage: ./cvat_download.sh SRC_DIR"
    exit 1
fi

SRC_DIR=$1
CONFIG_PATH=${SRC_DIR}/cvat-tup.cfg
CLASSES_JSON_PATH=${SRC_DIR}/classes.json

# Name of the directory that hosts this script.
DIR=$(dirname "${BASH_SOURCE[0]}")
# Full path to the directory that hosts this script.
DIRPATH=$(realpath "${DIR}")
# Path to the root directory.
PATH_ROOT=$(realpath "$DIRPATH/../")

HAVE_CONDA_ENV=false

# Configuration parameters
cvat_host_addr="localhost"
cvat_host_port=8080

# ANSI colors
INF="\e[32m"
IGN="\e[30m"
ERR="\e[31;1m"
RED="\e[31;1m"
END="\e[0m"

list_tasks() {
	python ${cvat_cli_path} --server-host ${cvat_host_addr} --server-port ${cvat_host_port} --auth ${cvat_credentials} ls
}

call_script_download() {
  local tasks=$1
  local directory=$2
  python ./bin/parse_filter.py --tasks ${tasks} --directory ${directory}
}

#activate_conda
#check_classes_json

echo -e "${INF}Loading configuration from ${CONFIG_PATH}.${END}"

if [ -f ${CONFIG_PATH} ]; then
	while read LINE; do declare "$LINE"; done < ${CONFIG_PATH}

	if [[ -z "${cvat_credentials}" ]]; then
		echo -e "${RED}Please provide 'credentials' for CVAT login, in ${CONFIG_PATH}${END}"
		exit 1
	fi
	if [[ -z "${cvat_cli_path}" ]]; then
		echo -e "${RED}Please provide the path to CVAT CLI utility, 'cvat_cli_path' in ${CONFIG_PATH}${END}"
		exit 1
	fi
else
	echo -e "${ERR}Missing configuration file, creating a template at ${CONFIG_PATH} ${END}"
	cp ${DIRPATH}/../share/config_template.cfg ${CONFIG_PATH}
	exit 1

fi

echo -e "${INF}Get list of existing tasks.${END}"
existing_tasks=$(list_tasks | grep ,)
echo -e "${INF}Call parse and filter script.${END}"
filtered_tasks=$(call_script_download "$existing_tasks" "$SRC_DIR")
echo $filtered_tasks