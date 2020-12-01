#!/bin/bash

# beginning of the main flow

HAVE_CONDA_ENV=false

# Configuration parameters
CONFIG_PATH=cvat_config/cvat-tup.cfg
#CLASSES_JSON_PATH=cvat_config/classes.json
cvat_host_addr="127.0.0.1"
cvat_host_port=8089

# ANSI colors
INF="\e[32m"
IGN="\e[30m"
ERR="\e[31;1m"
RED="\e[31;1m"
END="\e[0m"


list_tasks() {
	python ${cvat_cli_path} --server-host ${cvat_host_addr} --server-port ${cvat_host_port} --auth ${cvat_credentials} ls
}

call_python_parser() {
  local tasks=$1
  python parse_unlabelled.py --tasks ${tasks} --unlabeled
}


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
	cp $cvat_config/config_template.cfg ${CONFIG_PATH}
	exit 1

fi

echo -e "${INF}Credentials ${cvat_credentials} Cli path ${cvat_cli_path} others${END}"
echo -e "${INF}Get list of existing tasks.${END}"
existing_tasks=$(list_tasks | grep ,)
filtered_tasks=$(call_python_parser "$existing_tasks")
echo $filtered_tasks