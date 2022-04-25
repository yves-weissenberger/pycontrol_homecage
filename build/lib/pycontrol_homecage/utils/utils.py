import json
from typing import List, Tuple
import os
import re
import sys
import traceback
from datetime import datetime

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


def get_root_path() -> str:
    """ Read root path from config.json file"""
    return get_config()["ROOT"]


def get_paths() -> List[str]:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "prot"]
    return list(map(get_path, path_list))


def get_config() -> dict:
    config_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.json")
    config = json.load(open(config_path, 'r'))
    return config


def get_path(path_type) -> str:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "prot"]
    assert path_type in path_list, "PATH must be one of {}".format(path_list)
    return os.path.join(get_root_path(), path_type)


def get_pyhomecage_email() -> Tuple[str, str]:
    """ Return email and password of the system email account """
    lines_ = open(database.paths["user_path"], 'r').readlines()
    sender_email = re.findall('"(.*)"', [l_ for l_ in lines_ if 'system_email' in l_][0])[0]
    password = re.findall('"(.*)"', [l_ for l_ in lines_ if 'password' in l_][0])[0]
    return sender_email, password




def get_users() -> List[str]:
    dat = open(database.paths["user_path"], 'r').readlines()
    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    users = list(user_dict.keys())
    return users


def get_user_dicts() -> dict[str, str]:
    dat = open(user_path, 'r').readlines()

    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    return user_dict

