from distutils.core import setup
import json
from typing import List, Optional, Tuple
import os
import re
import sys
import traceback
from datetime import datetime

import pandas as pd

def custom_excepthook(type_, exception, traceback_, filepath):
    """ A custom exception hook that prints
        exceptions to a file so that they can then be used as alerts
        for an email daemon
    """
    now = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S')

    with open(filepath, 'a') as f:
        f.write('----------------- \n')
        f.write(repr(type_))
        f.write(repr(exception))
        traceback.print_exception(type_, exception, traceback_, file=f)
        f.write(now + '\n')
    sys._excepthook(type_, exception, traceback)

# --------------------------------------------------------------------------------
def get_user_path() -> str:
    return get_root_path() + "users.txt"

def get_root_path() -> str:
    """ Read root path from config.json file"""
    return get_config()["ROOT"]


def get_paths() -> List[str]:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "protocols"]
    return list(map(get_path, path_list))


def get_config() -> dict:
    config_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.json")
    config = json.load(open(config_path, 'r'))
    return config


def get_path(path_type) -> str:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "protocols", "users.txt"]
    assert path_type in path_list, "PATH must be one of {}".format(path_list)
    return os.path.join(get_root_path(), path_type)


def get_pyhomecage_email() -> Tuple[str, str]:
    """ Return email and password of the system email account """
    lines_ = open(get_path("users.txt"), 'r').readlines()
    sender_email = re.findall('system_email: "(.*)"password', [l_ for l_ in lines_ if 'system_email' in l_][0])[0]
    password = re.findall('password.*"(.*)"', [l_ for l_ in lines_ if 'password' in l_][0])[0]
    return sender_email, password




def get_users() -> List[str]:
    dat = open(get_path("users.txt"), 'r').readlines()
    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    users = list(user_dict.keys())
    return users


def get_user_dicts() -> dict[str, str]:
    dat = open(get_path("users.txt"), 'r').readlines()

    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    return user_dict


def load_data_csv() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    task_dir, experiment_dir, setup_dir, mice_dir = tuple(map(get_path,["tasks", "experiments", "setups", "mice"]))
    fp = os.path.join(task_dir, 'tasks.csv')
    task_df = pd.read_csv(fp)
    task_df.file_location = fp

    fp = os.path.join(experiment_dir, 'experiments.csv')
    exp_df = pd.read_csv(fp)
    exp_df.file_location = fp

    fp = os.path.join(setup_dir, 'setups.csv')
    setup_df = pd.read_csv(fp)
    setup_df.file_location = fp

    fp = os.path.join(mice_dir, 'mice.csv')
    mouse_df = pd.read_csv(fp)
    mouse_df.file_location = fp

    for col in mouse_df.columns:
        if 'unnamed' in col:
            mouse_df.drop(col, inplace=True, axis=1)

    return task_df, exp_df, setup_df, mouse_df
