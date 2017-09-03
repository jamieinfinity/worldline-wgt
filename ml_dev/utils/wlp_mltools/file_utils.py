import os
import csv
import json


def _get_filenames(dir_path, basename):
    onlyfiles = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    return [dir_path + x for x in onlyfiles if basename in x]


def _get_json_data(filename, **kwargs):
    data_dump = []
    with open(filename, encoding='utf8') as jsonfile:
        d = json.load(jsonfile)
        if 'dict_key' in kwargs:
            data_dump.extend(d[kwargs['dict_key']])
        else:
            data_dump.extend(d)
    return data_dump


def get_json_data(dir_path, basename, **kwargs):
    datadump = []
    files = _get_filenames(dir_path, basename)
    [datadump.extend(_get_json_data(filename, **kwargs)) for filename in files]
    return datadump


def _get_csv_data(filename):
    datadump = []
    with open(filename, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            datadump.append(row)
    return datadump


def get_csv_data(dir_path, basename):
    datadump = []
    files = _get_filenames(dir_path, basename)
    [datadump.extend(_get_csv_data(filename)) for filename in files]
    return datadump
