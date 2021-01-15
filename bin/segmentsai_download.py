#!/usr/bin/env python3
# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab

# Copyright 2020 - 2021 KappaZeta Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pathlib
import datetime
import json
import requests
import urllib.request
import sys
import argparse
import glob
import os
import re
from segments import SegmentsClient


SAI_MASK_FNAME = "segments_ai_classification_mask.png"
SAI_CLASSES_FNAME = "segments_ai_classes.json"



class LinuxLogColorFormatter(logging.Formatter):
    """
    Python logging color formatter.
    http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """
    FORMAT = ("[%(levelname)-18s][%(name)-4s]  "
              "%(message)s "
              "($BOLD%(filename)s$RESET:%(lineno)d)")
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    COLORS = {
        'WARNING': YELLOW,
        'INFO': WHITE,
        'DEBUG': BLUE,
        'CRITICAL': YELLOW,
        'ERROR': RED,
        'RED': RED,
        'GREEN': GREEN,
        'YELLOW': YELLOW,
        'BLUE': BLUE,
        'MAGENTA': MAGENTA,
        'CYAN': CYAN,
        'WHITE': WHITE,
    }

    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    def __init__(self, use_color=True):
        """Initialize the formatter."""
        self.use_color = use_color
        if use_color:
            msg = self.FORMAT.replace("$RESET", self.RESET_SEQ).replace("$BOLD", self.BOLD_SEQ)
        else:
            msg = self.FORMAT.replace("$RESET", "").replace("$BOLD", "")

        logging.Formatter.__init__(self, msg)

    def format(self, record):
        """Format a log record."""
        levelname = record.levelname
        if self.use_color and levelname in self.COLORS:
            fg_color = 30 + self.COLORS[levelname]
            levelname_color = self.COLOR_SEQ % fg_color + levelname + self.RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class LogInfoFilter(logging.Filter):
    """A logging filter that discards warnings and errors."""
    def filter(self, record):
        """False on warning or error records."""
        return record.levelno in (logging.DEBUG, logging.INFO)


class Loggable(object):
    """A class that uses the logging functionality."""
    def __init__(self, log_module_abbrev):
        self.log = logging.getLogger(log_module_abbrev)


def init_logging(verbosity, app_name, app_abbrev, logfile):
    """Initialize logging, based on verbosity level."""
    # Configure logging
    if verbosity == None:
        log_level = logging.NOTSET
    elif verbosity == 0:
        log_level = logging.WARNING
    elif verbosity == 1:
        log_level = logging.INFO
    elif verbosity > 2:
        log_level = logging.DEBUG
    else:
        log_level = logging.NOTSET
   
    log = logging.getLogger(app_abbrev)
    log.setLevel(log_level)

    # Create log formatters.
    log_formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(name)s: %(message)s')
    if os.name != 'nt':
        stdout_formatter = LinuxLogColorFormatter()
    else:
        # For colored output in Windows, refer to sorin's answer in
        # http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
        stdout_formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')

    # Info, debug messages to stdout (if we have enough verbosity).
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.addFilter(LogInfoFilter())
    log.addHandler(stdout_handler)

    # Warnings and errors to stderr.
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(stdout_formatter)
    log.addHandler(stderr_handler)

    # Regular log file.
    if logfile:
        # Create the directory tree if it doesn't exist yet.
        dirpath = os.path.dirname(os.path.abspath(logfile))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        log_handler = logging.FileHandler(logfile)
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(log_formatter)
        log.addHandler(log_handler)

    return log


class SegmentsAIClient(object):
    """
    Thin wrapper around SegmentsClient.
    """
    def __init__(self, api_key):
        self.api_key = api_key

        self.client = SegmentsClient(self.api_key)

    def list_datasets(self, user):
        """List public datasets published by a user."""
        return self.client.get_datasets(user)

    def get_dataset(self, user, dataset):
        """Get a dataset from a user."""
        return self.client.get_dataset("{}/{}".format(user, dataset))

    def list_samples(self, user, dataset):
        """List samples in a dataset."""
        return self.client.get_samples("{}/{}".format(user, dataset))

    def get_samples(self, uuids):
        """Get samples with the listed UUIDs."""
        dl_samples = []

        for uuid in uuids:
            dl_samples.append(self.client.get_sample(uuid=uuid))

        return dl_samples

    def get_labels(self, sample_uuids, labelsets):
        """Get labels for samples with the listed UUIDs, from the listed labelsets / tasks (ground-truth, model-predictions, etc.)."""
        l_labels = []
        if isinstance(sample_uuids, list):
            for sample in sample_uuids:
                for ls in labelsets:
                    l_labels.append(self.client.get_label(sample, ls))
        else:
            for ls in labelsets:
                l_labels.append(self.client.get_label(sample_uuids, ls))
        return l_labels

    def filter_labels(self, labels, status=None):
        """Filter labels by a list of statuses (LABELED, REVIEWED)."""
        labels_f = []
        if status is not None and isinstance(status, list):
            for l in labels:
                if "label_status" not in l.keys():
                    print(l)
                elif l["label_status"] in status:
                    labels_f.append(l)
        labels = labels_f
        return labels

    def filter_labelsets(self, labelsets, names=None):
        """Filter labelsets by a list of names."""
        l_labelsets = []

        if names is None:
            return labelsets

        for ls in labelsets:
            if isinstance(names, list) and ls["name"] in names:
                l_labelsets.append(ls)
            elif ls["name"] == names:
                l_labelsets.append(ls)

        return l_labelsets

    def filter_samples(self, samples, names=None):
        """Filter samples by a list of names."""
        l_samples = []

        if name is None:
            return samples

        for s in samples:
            if isinstance(names, list) and s["name"] in names:
                l_samples.append(s)
            elif s["name"] == names:
                l_samples.append(s)

        return l_samples

    def download_segmentation_bitmap(self, label, path):
        """Download the segmentation bitmap of a label, and store it at the provided path."""
        return urllib.request.urlretrieve(label['attributes']["segmentation_bitmap"]["url"], path)

    def save_class_legend(self, ds, label, path, labelsets):
        """Save class legend into a JSON file."""
        f_ls = self.filter_labelsets(ds["tasks"], names=labelsets)

        # Take the map of categories from the first labelset.
        categories = f_ls[0]["attributes"]["categories"]
        # Build a simple dictionary for the JSON file.
        d = {
            "format_version": "0.0.1",
            "uuid": label["uuid"],
            "label_status": label["label_status"],
            "label_map": label["attributes"]["annotations"]
        }
        # Assign category names, based on category_id.
        for a_id in d["label_map"]:
            for c in categories:
                if c["id"] == a_id["category_id"]:
                    a_id["category_name"] = c["name"]

        with open(path, "w") as fo:
            json.dump(d, fo)


def get_file_mtime(path):
    """Get the modified time of a file at the given path."""
    return datetime.datetime.fromtimestamp(pathlib.Path(path).stat().st_mtime)


def str_to_datetime(text):
    """Convert string to datetime."""
    return datetime.datetime.fromisoformat(text.replace("Z", ""))

def scan_cvat_dir(path):
    """Scan a CVAT directory for true-color images which might've been uploaded to Segments.AI."""
    tiles = []

    for fpath in glob.iglob(path + "/tile_*/*_TCI_*.png", recursive=True):
        if os.path.isfile(fpath):
            # Check if there's already a classification mask stored in the subtile directory.
            path_classification_mask = os.path.join(os.path.dirname(fpath), SAI_MASK_FNAME)
            date_classification_mask = None
            if os.path.isfile(path_classification_mask):
                date_classification_mask = get_file_mtime(path_classification_mask)

            d = {
                "name": os.path.basename(fpath),
                "path": fpath,
                # The modified time of the existing classification mask (if any)
                "modified": date_classification_mask
            }
            tiles.append(d)
    return tiles


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Perform common operations related to Segments.AI tasks.\n\n'
    )
    p.add_argument("cvat_dir", action="store", help="Path to a Sentinel-2 product preprocessed with CVAT-VSM.")
    p.add_argument("api_key", action="store", help="Segments.AI API key.")
    p.add_argument("username", action="store", help="Segments.AI username which hosts the labelled datasets.")
    p.add_argument("labelsets", action="store", help="Segments.AI comma-separated list of tasks / labelsets to check.")
    p.add_argument("-l", "--log", dest="log_path", action="store", default=None, help="Path to log file.")

    args = p.parse_args()

    log = init_logging(1, "Segments.AI Downloader", "SAID", args.log_path)

    labelsets = [s.strip() for s in args.labelsets.split(",")]

    log.info("Scanning for tiles in {}".format(args.cvat_dir))
    tiles = scan_cvat_dir(args.cvat_dir)

    # Extract the tile name from the end of the CVAT directory path.
    m = re.match(r".*_([0-9A-Z]+_[T\d]+)\.CVAT", args.cvat_dir)
    if m:
        tile_name = m.group(1)
        # Assume that all datasets follow the example of "cloudmask_T35VND_20200824T121941".
        dataset_name = "cloudmask_" + tile_name

        log.info("Connecting to Segments.AI with key \"{}\"".format(args.api_key))
        sai = SegmentsAIClient(args.api_key)

        log.info("Looking for dataset \"{}\" from user \"{}\"".format(dataset_name, args.username))
        ds = sai.get_dataset(args.username, dataset_name)

        log.info("Fetching list of samples")
        l_samples = sai.list_samples(args.username, dataset_name)

        # Get tiles which have a corresponding sample.
        for t in tiles:
            t_dir = os.path.dirname(t["path"])
            for s in l_samples:
                if t["name"] == s["name"]:
                    log.info("Fetching labels for {}".format(t["path"]))

                    l_labels = sai.get_labels(s["uuid"], labelsets)
                    f_labels = sai.filter_labels(l_labels, status=["LABELED", "REVIEWED"])

                    for l in f_labels:
                        # Skip if we already have the file and it's recent enough.
                        if t["modified"] and t["modified"] >= str_to_datetime(l["updated_at"]):
                            log.info("Skipping, already up to date ({} vs {})".format(l["updated_at"], t["modified"]))
                            continue

                        # Download segmentation mask bitmap.
                        try:
                            sai.download_segmentation_bitmap(l, os.path.join(t_dir, SAI_MASK_FNAME))
                        except Exception as e:
                            log.exception("Failed to download segmentation bitmap")
                        # Save color index - class mappings.
                        sai.save_class_legend(ds, l, os.path.join(t_dir, SAI_CLASSES_FNAME), labelsets)

    log.info("Done")

