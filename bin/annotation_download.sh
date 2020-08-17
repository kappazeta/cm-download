#!/bin/bash

# beginning of the main flow

SRC_DIR=$1
TASK_ID=$2
TEMP_PATH=$3
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


download_annotation() {
  python ${cvat_cli_path} --server-host ${cvat_host_addr} --server-port ${cvat_host_port} --auth ${cvat_credentials} dump ${TASK_ID} ${TEMP_PATH} | grep -o finished
  echo $(dirname ${TEMP_PATH})
  unzip ${TEMP_PATH} -d $(dirname ${TEMP_PATH})
}

if [ -f ${TEMP_PATH} ]; then
    echo -e "${INF} $TEMP_PATH exists.${END}"
else
    echo -e "${INF} $TEMP_PATH does not exist.${END}"
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

    echo -e "${INF}Downloading annotation from CVAT.${END}"
    existing_tasks=$(download_annotation)
    echo $existing_tasks
fi
