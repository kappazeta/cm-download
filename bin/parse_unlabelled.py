#!/usr/bin/env python3
import logging
import json
import requests
import sys
import argparse
import subprocess
import os
log = logging.getLogger(__name__)


def check_status(item):
    """ Check if identifiers and date are the same and status completed """
    if item[2] == 'annotation':
        return True
    else:
        return False


def parse_filter_unlabelled(task_output):
    """ Filter and match jobs and output full task list, task ids and paths for downloading """
    task_list = []
    for item in task_output:
        item = item.split(",")
        if len(item) == 3:
            if check_status(item):
                task_list.append(item)

    return task_list


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
        '--unlabelled',
        help='mode'
    )
    args, unknown = parser.parse_known_args()
    task_list = parse_filter_unlabelled(unknown)

    # Write task list to file if needed
    if not os.path.exists('output'):
        os.mkdir('output')
    with open('output/unlabelled_tasks.txt', 'w') as f:
        for task in task_list:
            for item in task:
                f.write(item)
                f.write(",")
            f.write("\n")
