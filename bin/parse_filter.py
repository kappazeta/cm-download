#!/usr/bin/env python3
import logging
import json
import requests
import sys
import argparse
import subprocess
log = logging.getLogger(__name__)


def get_identifiers(path_file):
    """ Get unique identifier and date of file """
    file_specificator = path_file.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    date_match = file_specificator.rsplit('_', 1)[-1]
    index_match = file_specificator.rsplit('_', 1)[0].rsplit('_', 1)[-1]
    return date_match, index_match


def check_match_file(item, date_match, index_match):
    """ Check if identifiers and date are the same and status completed """
    splitted_name = item[1].split("_")
    if splitted_name[1] == index_match and splitted_name[2] == date_match and item[2] == 'completed':
        return True
    else:
        return False


def get_tile_folder(item):
    """ Get which part of tile it is as folder name """
    splitted_name = item[1].rsplit('_', 3)
    folder_str = '_'.join(map(str, splitted_name[1:4]))
    return folder_str


def get_task_id(item):
    """ Get task_id of job """
    return item[0]


def parse_filter_names(task_output, date_match, index_match):
    """ Filter and match jobs and output full task list, task ids and paths for downloading """
    task_list = []
    task_ids = []
    list_full_path = []
    for item in task_output:
        item = item.split(",")
        if len(item) == 3:
            if check_match_file(item, date_match, index_match):
                folder_str = get_tile_folder(item)
                task_id = get_task_id(item)
                curr_path = args.directory + '/' + folder_str + '/annotations.zip'

                task_list.append(item)
                task_ids.append(task_id)
                list_full_path.append(curr_path)
    return task_list, task_ids, list_full_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Perform common operations related to CVAT tasks.\n\n'
    )
    parser.add_argument(
        '--tasks',
        default="",
        help='all existed tasks'
    )
    parser.add_argument(
        '--directory',
        help='data directory'
    )
    args, unknown = parser.parse_known_args()
    date_match, index_match = get_identifiers(args.directory)
    task_list, task_ids, save_path = parse_filter_names(unknown, date_match, index_match)

    # Write task list to file if needed
    with open('output/filtered_tasks.txt', 'w') as f:
        for task in task_list:
            for item in task:
                f.write(item)
                f.write(",")
            f.write("\n")

    for count, id in enumerate(task_ids):
        #task_id = 313 # 313,S2A_T35VME_20200509T111504_tile_256_2816,completed,
        subprocess.check_call(['bin/annotation_download.sh', args.directory, id, save_path[count]])



